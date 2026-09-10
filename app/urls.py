from django.urls import path
from django.shortcuts import render
from django.http import HttpResponse
from app.views.categorias import views as cat_views
from app.views.proveedores import views as prov_views
from app.views.marca import views as mar_views  # type: ignore
from app.views.bodega import views as bod_views

def inicio(request):
    return render(request, 'base/base.html')

urlpatterns = [
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

    # Rutas auxiliares
    path('stock-status/', lambda r: HttpResponse('OK'), name='stock_status'),
    path('perfil/', lambda r: HttpResponse('Perfil'), name='perfil_pagina'),
    path('usuarios/', lambda r: HttpResponse('Usuarios'), name='usuario'),

    # MARCAS
    path('marcas/', mar_views.lista_marcas, name='lista_marcas'),  # type: ignore
    path('marcas/crear/', mar_views.crear_marca, name='crear_marca'),  # type: ignore
    path('marcas/editar/<str:codigo_marca>/', mar_views.editar_marca, name='editar_marca'),  # type: ignore
    path('marcas/eliminar/<str:codigo_marca>/', mar_views.eliminar_marca, name='eliminar_marca'),  # type: ignore

    # BODEGA
    path('bodega/', bod_views.bodega_home, name='bodega_home'),
    path('bodega/agenda/', bod_views.agenda_list, name='agenda_list'),
    path('bodega/agenda/nueva/', bod_views.agenda_create, name='agenda_create'),
    path('bodega/agenda/<int:codigo>/', bod_views.agenda_detail, name='agenda_detail'),
    path('bodega/agenda/<int:codigo>/editar/', bod_views.agenda_update, name='agenda_update'),
    path('bodega/agenda/<int:codigo>/completar/', bod_views.agenda_completar, name='agenda_completar'),
    path('bodega/agenda/<int:codigo_agenda>/hallazgo/', bod_views.hallazgo_create, name='hallazgo_create'),
    path('bodega/hallazgos/', bod_views.hallazgo_list, name='hallazgo_list'),
    path('bodega/ajustar-stock/<int:pk>/', bod_views.ajustar_stock, name='ajustar_stock'),
]