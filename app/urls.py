from django.urls import path
from django.shortcuts import render
from django.http import HttpResponse
from app.views.categorias import views as cat_views
from app.views.proveedores import views as prov_views
from app.views.marca import views as mar_views  # type: ignore

# ── VISTA PRINCIPAL (Muestra tu esqueleto de partials: Header + Aside + Base) ──
def inicio(request):
    return render(request, 'partials/base.html')


urlpatterns = [
    # ── PÁGINA PRINCIPAL / TABLERO (http://127.0.0.1:8000/) ──
    path('', inicio, name='principal'),

    # CATEGORIAS
    path('categorias/', cat_views.categorias_lista, name='categorias_lista'),
    path('crear/', cat_views.categoria_crear, name='crear'),
    path('editar/<int:pk>/', cat_views.categoria_editar, name='editar'),
    path('eliminar/<int:pk>/', cat_views.categoria_eliminar, name='eliminar'),

    # PROVEEDORES
    path('proveedores/', prov_views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/crear/', prov_views.crear_proveedor, name='crear_proveedor'),
    path('proveedores/detalle/<str:id>/', prov_views.detalle_proveedor, name='detalle_proveedor'),
    path('proveedores/editar/<str:id>/', prov_views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<str:id>/', prov_views.eliminar_proveedor, name='eliminar_proveedor'),
    path('proveedores/activar/<str:id>/', prov_views.activar_proveedor, name='activar_proveedor'),
    path('proveedores/desactivar/<str:id>/', prov_views.desactivar_proveedor, name='desactivar_proveedor'),
    path('proveedores/sancionar/<str:id>/', prov_views.sancionar_proveedor, name='sancionar_proveedor'),
    path('proveedores/levantar-sancion/<str:id>/', prov_views.levantar_sancion_proveedor, name='levantar_sancion_proveedor'),

    # Modales / AJAX Proveedores
    path('proveedores/modal/detalle/<str:id>/', prov_views.detalle_proveedor_modal, name='detalle_proveedor_modal'),
    path('proveedores/modal/desactivar/<str:id>/', prov_views.desactivar_proveedor_modal, name='desactivar_proveedor_modal'),
    path('proveedores/modal/reactivar/<str:id>/', prov_views.reactivar_proveedor_modal, name='reactivar_proveedor_modal'),
    path('proveedores/modal/sancionar/<str:id>/', prov_views.sancionar_proveedor_modal, name='sancionar_proveedor_modal'),

    # Rutas auxiliares (para que los enlaces de tu header y aside no den error)
    path('stock-status/', lambda r: HttpResponse('OK'), name='stock_status'),
    path('perfil/', lambda r: HttpResponse('Perfil'), name='perfil_pagina'),
    path('usuarios/', lambda r: HttpResponse('Usuarios'), name='usuario'),
    
       # MARCAS
    path('marcas/', mar_views.lista_marcas, name='lista_marcas'), # type: ignore
    path('marcas/crear/', mar_views.crear_marca, name='crear_marca'), # type: ignore
    path('marcas/editar/<str:codigo_marca>/', mar_views.editar_marca, name='editar_marca'), # type: ignore
    path('marcas/eliminar/<str:codigo_marca>/', mar_views.eliminar_marca, name='eliminar_marca'), # type: ignore

]
