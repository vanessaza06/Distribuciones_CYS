import json
import math
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from app.models import Caja, AperturaCaja, CierreCaja, Venta
from app.views.ventas.views import obtener_caja_abierta

Usuario = get_user_model()


class CajaModuleTests(TestCase):
    """
    Pruebas unitarias completas para el módulo de Caja:
    - Verificación de autenticación y autorización (@session_required & LoginRequiredMiddleware).
    - Apertura de caja con montos válidos y denominaciones.
    - Rechazo de montos negativos y formatos erróneos.
    - Sincronización relacional con AperturaCaja y CierreCaja.
    - Registro de conteo de arqueo y cierre estricto de caja.
    - Prevención de cierres duplicados o sin turno abierto.
    - Cálculo de transferencias y ventas en el cierre.
    """

    def setUp(self):
        # Crear usuario autenticado para pruebas
        self.user = Usuario.objects.create_user(
            username='cajero_test',
            identificacion='1098765432',
            first_name='Cajero',
            last_name='Prueba',
            email='cajero@distribuidora.com',
            password='Password123!',
            rol='cajero',
        )
        self.client.force_login(self.user)

    def test_apertura_sin_sesion_ajax_retorna_401(self):
        """Petición AJAX sin sesión retorna 401 JSON."""
        self.client.logout()
        payload = {'monto_base': 150000, 'denominaciones': {'50000': 3}}
        resp = self.client.post(
            reverse('apertura_caja'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(resp.status_code, 401)
        data = resp.json()
        self.assertIn('No autenticado', data.get('error', '') or '')

    def test_cierre_sin_sesion_ajax_retorna_401(self):
        """Petición AJAX sin sesión al cierre retorna 401 JSON."""
        self.client.logout()
        payload = {'total_contado': 200000, 'total_retirado': 50000}
        resp = self.client.post(
            reverse('cierre_caja'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(resp.status_code, 401)
        data = resp.json()
        self.assertIn('No autenticado', data.get('error', '') or '')

    def test_sin_sesion_navegador_redirige_a_login(self):
        """Petición estándar de navegador sin sesión redirige a /login (302)."""
        self.client.logout()
        resp = self.client.get(reverse('caja'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('login'), resp.headers['Location'])

    def test_apertura_metodo_get_no_permitido(self):
        """El endpoint apertura_caja rechaza solicitudes GET con 405."""
        resp = self.client.get(reverse('apertura_caja'))
        self.assertEqual(resp.status_code, 405)

    def test_cierre_metodo_get_no_permitido(self):
        """El endpoint cierre_caja rechaza solicitudes GET con 405."""
        resp = self.client.get(reverse('cierre_caja'))
        self.assertEqual(resp.status_code, 405)

    def test_apertura_json_invalido_retorna_400(self):
        """Payload malformado retorna 400 Bad Request."""
        resp = self.client.post(
            reverse('apertura_caja'),
            data='{json_corrupto',
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json().get('ok'))

    def test_apertura_denominacion_negativa_rechazada(self):
        """No se permiten cantidades negativas en denominaciones."""
        payload = {
            'monto_base': 100000,
            'denominaciones': {'50000': -2, '10000': 1},
        }
        resp = self.client.post(
            reverse('apertura_caja'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('No se permiten cantidades negativas', resp.json().get('error', ''))

    def test_apertura_monto_base_negativo_rechazada(self):
        """No se permite abrir caja con monto base negativo."""
        payload = {
            'monto_base': -50000,
            'denominaciones': {},
        }
        resp = self.client.post(
            reverse('apertura_caja'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('monto base negativo', resp.json().get('error', ''))

    def test_apertura_caja_exitosa_y_sincronizacion(self):
        """Apertura exitosa genera registro en Caja y sincroniza AperturaCaja."""
        payload = {
            'monto_base': 250000,
            'observacion': 'Turno de la mañana',
            'denominaciones': {'50000': 4, '20000': 2, '10000': 1},
        }
        resp = self.client.post(
            reverse('apertura_caja'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('monto_base'), 250000)

        # Verificar en base de datos
        caja_activa = obtener_caja_abierta()
        self.assertIsNotNone(caja_activa)
        self.assertEqual(caja_activa.monto_base, Decimal('250000'))
        self.assertNotIn('[CERRADO]', caja_activa.observacion or '')

        # Verificar AperturaCaja
        apertura_reg = AperturaCaja.objects.filter(fecha=timezone.localdate()).first()
        self.assertIsNotNone(apertura_reg)
        self.assertEqual(apertura_reg.monto_base, Decimal('250000'))

    def test_cierre_caja_sin_caja_abierta_retorna_400(self):
        """Intentar cerrar caja cuando no hay ninguna abierta retorna error 400."""
        # Aseguramos que cualquier caja existente esté cerrada
        Caja.objects.all().update(observacion='[CERRADO]')
        self.assertIsNone(obtener_caja_abierta())

        payload = {
            'total_contado': 300000,
            'total_retirado': 100000,
            'monto_base_siguiente': 200000,
        }
        resp = self.client.post(
            reverse('cierre_caja'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertFalse(data.get('ok'))
        self.assertEqual(data.get('error'), 'No hay un turno de caja abierto para cerrar.')

    def test_cierre_caja_montos_negativos_rechazados(self):
        """Valores negativos en arqueo de cierre son rechazados con 400."""
        # Abrir caja primero
        caja = Caja.objects.create(
            fecha_hora=timezone.now(),
            monto_base=Decimal('100000'),
            total_efectivo=Decimal('0'),
            total_transferencias=Decimal('0'),
            total_retirado=Decimal('0'),
            observacion='Turno prueba',
        )
        self.assertIsNotNone(obtener_caja_abierta())

        payload = {
            'total_contado': -500,
            'total_retirado': 10000,
            'monto_base_siguiente': 50000,
        }
        resp = self.client.post(
            reverse('cierre_caja'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('No se permiten valores negativos', resp.json().get('error', ''))

    def test_cierre_caja_exitoso_y_calculo_transferencias(self):
        """Cierre de caja exitoso marca turno como cerrado y sincroniza CierreCaja."""
        # 1. Crear caja abierta
        caja = Caja.objects.create(
            fecha_hora=timezone.now(),
            monto_base=Decimal('150000'),
            total_efectivo=Decimal('0'),
            total_transferencias=Decimal('0'),
            total_retirado=Decimal('0'),
            observacion='Turno vespertino',
        )

        # 2. Asociar ventas al turno con pago mixto
        Venta.objects.create(
            caja=caja,
            fecha=timezone.now(),
            total_venta=Decimal('80000'),
            pago_efectivo=Decimal('50000'),
            pago_nequi=Decimal('30000'),
            vendedor=self.user,
        )

        # 3. Ejecutar cierre
        payload = {
            'total_contado': 200000,
            'total_retirado': 100000,
            'monto_base_siguiente': 100000,
            'denominaciones': {'50000': 4},
        }
        resp = self.client.post(
            reverse('cierre_caja'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('total_efectivo'), 200000)
        self.assertEqual(data.get('total_retirado'), 100000)
        self.assertEqual(data.get('total_transferencias'), 30000)

        # Verificar que la caja quedó cerrada
        caja.refresh_from_db()
        self.assertIn('[CERRADO]', caja.observacion)
        self.assertEqual(caja.total_efectivo, Decimal('200000'))
        self.assertEqual(caja.total_retirado, Decimal('100000'))
        self.assertEqual(caja.total_transferencias, Decimal('30000'))
        self.assertIsNone(obtener_caja_abierta())

    def test_vista_caja_dashboard_status_200(self):
        """La vista principal de caja (/caja/) carga correctamente con código 200."""
        # Crear un turno histórico cerrado y uno activo
        Caja.objects.create(
            fecha_hora=timezone.now() - timezone.timedelta(days=1),
            monto_base=Decimal('100000'),
            total_efectivo=Decimal('150000'),
            total_retirado=Decimal('50000'),
            total_transferencias=Decimal('0'),
            observacion='Turno Ayer [CERRADO]',
        )
        Caja.objects.create(
            fecha_hora=timezone.now(),
            monto_base=Decimal('100000'),
            total_efectivo=Decimal('0'),
            total_retirado=Decimal('0'),
            total_transferencias=Decimal('0'),
            observacion='Turno Hoy',
        )

        resp = self.client.get(reverse('caja'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Control de Caja y Turnos')
        self.assertContains(resp, 'modalConteo')
        self.assertContains(resp, 'modalCierre')
