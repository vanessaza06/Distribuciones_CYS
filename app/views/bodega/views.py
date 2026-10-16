from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldDoesNotExist
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from app.models import Producto, PresentacionProducto, AgendaInventario, Lote
from app.forms import AgendaInventarioForm


# Campos que identifican a la misma persona en las dos tablas de usuarios.
# Van de más a menos confiable; el pk NO se usa porque dos tablas distintas
# pueden tener el mismo id para personas distintas.
_CAMPOS_IDENTIDAD = ('documento', 'correo', 'email', 'username')


def _usuario_para(modelo, campo, user):
    """
    Devuelve la instancia que la FK `campo` de `modelo` espera para `user`,
    o None si no existe un registro equivalente.
    """
    relacionado = modelo._meta.get_field(campo).related_model

    if isinstance(user, relacionado):
        return user

    for nombre in _CAMPOS_IDENTIDAD:
        try:
            relacionado._meta.get_field(nombre)
        except FieldDoesNotExist:
            continue
        valor = getattr(user, nombre, None)
        if valor:
            encontrado = relacionado.objects.filter(**{nombre: valor}).first()
            if encontrado:
                return encontrado

    return None


def _fk_admite_null(modelo, campo):
    return modelo._meta.get_field(campo).null


def _validar_agenda(titulo, fecha_texto, descripcion):
    """Valida los datos del formulario 'Agendar'. Devuelve (errores, fecha)."""
    errores = []
    fecha = None

    if len(titulo) < 3:
        errores.append('El título debe tener al menos 3 caracteres.')
    elif len(titulo) > 100:
        errores.append('El título no puede superar los 100 caracteres.')

    if not fecha_texto:
        errores.append('Selecciona la fecha y la hora del inventario.')
    else:
        try:
            fecha = datetime.strptime(fecha_texto, '%Y-%m-%dT%H:%M')
            if timezone.is_naive(fecha):
                fecha = timezone.make_aware(fecha)
            if fecha < timezone.now() - timedelta(minutes=1):
                errores.append('La fecha y hora no pueden estar en el pasado.')
        except ValueError:
            errores.append('La fecha no es válida.')

    if len(descripcion) > 300:
        errores.append('La descripción no puede superar los 300 caracteres.')

    return errores, fecha


@login_required
def bodega_home(request):
    if request.method == 'POST' and 'Agendar' in request.POST:
        titulo = (request.POST.get('titulo') or '').strip()
        fecha_texto = (request.POST.get('fecha_programada') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip()

        errores, fecha_programada = _validar_agenda(titulo, fecha_texto, descripcion)
        if errores:
            for e in errores:
                messages.error(request, e)
            return redirect('bodega_home')

        # documento_usuario admite null: si no hay equivalente, se guarda sin usuario.
        usuario = _usuario_para(AgendaInventario, 'documento_usuario', request.user)
        if usuario is None and not _fk_admite_null(AgendaInventario, 'documento_usuario'):
            messages.error(request, 'No se encontró tu usuario para registrar la agenda.')
            return redirect('bodega_home')

        AgendaInventario.objects.create(
            titulo=titulo,
            fecha=fecha_programada,  # el campo del modelo se llama "fecha"
            descripcion=descripcion,
            documento_usuario=usuario,
        )
        messages.success(request, "Inventario programado correctamente.")
        return redirect('bodega_home')

    agendas = AgendaInventario.objects.all()
    lotes = Lote.objects.select_related('presentacion__producto', 'bodega').all()

    # Presentaciones activas que todavía no tienen ningún lote registrado.
    # Al crear una presentación nueva, aparecerá aquí automáticamente.
    presentaciones_sin_lote = (
        PresentacionProducto.objects
        .filter(activo=True, lotes__isnull=True)
        .select_related('producto', 'producto__categoria')
        .order_by('producto__nombre', 'nombre')
    )

    context = {
        'agendas': agendas,
        'productos': Producto.objects.all(),
        'lotes': lotes,
        'presentaciones_sin_lote': presentaciones_sin_lote,
        'conteos': [],
        'discrepancias': [],
        'sesion': None,
    }
    return render(request, 'bodega/bodega_home.html', context)


@login_required
def agenda_list(request):
    estado = request.GET.get('estado')
    agendas = AgendaInventario.objects.select_related('documento_usuario', 'responsable')
    if estado:
        agendas = agendas.filter(estado=estado)
    return render(request, 'bodega/agenda_list.html', {'agendas': agendas, 'estado': estado})


@login_required
def agenda_create(request):
    if request.method == 'POST':
        form = AgendaInventarioForm(request.POST)
        if form.is_valid():
            usuario = _usuario_para(AgendaInventario, 'documento_usuario', request.user)
            if usuario is None and not _fk_admite_null(AgendaInventario, 'documento_usuario'):
                messages.error(request, 'No se encontró tu usuario para registrar la agenda.')
                return redirect('bodega_home')
            agenda = form.save(commit=False)
            agenda.documento_usuario = usuario
            agenda.save()
            messages.success(request, f'Agenda "{agenda.titulo}" creada.')
            return redirect('bodega_home')
    else:
        form = AgendaInventarioForm()
    return render(request, 'bodega/agenda_form.html', {'form': form})


@login_required
def agenda_update(request, codigo):
    agenda = get_object_or_404(AgendaInventario, pk=codigo)
    if request.method == 'POST':
        if 'estado' in request.POST:
            nuevo_estado = request.POST.get('estado')
            estados_validos = {valor for valor, _ in AgendaInventario.ESTADO_CHOICES}
            if nuevo_estado not in estados_validos:
                messages.error(request, 'El estado seleccionado no es válido.')
                return redirect('bodega_home')

            agenda.estado = nuevo_estado
            if agenda.estado == 'completada':
                usuario = _usuario_para(AgendaInventario, 'completado_por', request.user)
                if usuario is not None:
                    agenda.completado_por = usuario
            agenda.save()
            messages.success(request, "Estado de agenda actualizado.")
            return redirect('bodega_home')

        form = AgendaInventarioForm(request.POST, instance=agenda)
        if form.is_valid():
            form.save()
            return redirect('bodega_home')
    else:
        form = AgendaInventarioForm(instance=agenda)
    return render(request, 'bodega/agenda_form.html', {'form': form, 'agenda': agenda})


@login_required
def agenda_detail(request, codigo):
    agenda = get_object_or_404(AgendaInventario, pk=codigo)
    return render(request, 'bodega/agenda_detail.html', {'agenda': agenda})


@login_required
def agenda_completar(request, codigo):
    agenda = get_object_or_404(AgendaInventario, pk=codigo)
    agenda.estado = 'completada'
    usuario = _usuario_para(AgendaInventario, 'completado_por', request.user)
    if usuario is not None:
        agenda.completado_por = usuario
    agenda.save()
    messages.success(request, f'Agenda "{agenda.titulo}" completada.')
    return redirect('bodega_home')


@login_required
def ajustar_stock(request, pk):
    """Referenciada desde el modal 'Comparar Inventario' de bodega_home.html."""
    presentacion = get_object_or_404(PresentacionProducto, pk=pk)
    if request.method == 'POST':
        try:
            nueva_cantidad = int(request.POST.get('nueva_cantidad', ''))
            if nueva_cantidad < 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, 'La cantidad ingresada no es válida.')
            return redirect('bodega_home')

        presentacion.cantidad = nueva_cantidad
        presentacion.save()
        messages.success(request, f'Stock de "{presentacion.producto.nombre}" ajustado correctamente.')
    return redirect('bodega_home')