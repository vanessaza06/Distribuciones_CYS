from django.urls import path
from django.shortcuts import render
from django.http import HttpResponse
from app.views.categorias import views as cat_views
from app.views.proveedores import views as prov_views
from app.views.marca import views as mar_views  # type: ignore
from app.views.productos import views as prod_views
from app.views.presentaciones import views as pres_views
from app.views.lotes import views as lot_views
from app.views.detalle_producto import views as deta_views

def inicio(request):
    return render(request, 'base/base.html')

urlpatterns = [
    path('', inicio, name='principal'),

    # CATEGORIAS
    path('categorias/', cat_views.categorias_lista, name='categorias_lista'),
    path('crear/', cat_views.categoria_crear, name='crear'),
    path('editar/<int:pk>/', cat_views.categoria_editar, name='editar'),
    path('eliminar/<int:pk>/', cat_views.categoria_eliminar, name='eliminar'),
    path('categorias/<int:pk>/toggle/', cat_views.categoria_toggle_activo, name='categoria_toggle_activo'),

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

    # Rutas auxiliares (quitamos 'perfil_pagina' y 'usuario', ahora vienen del módulo usuarios)
    path('stock-status/', lambda r: HttpResponse('OK'), name='stock_status'),
    path('perfil/', lambda r: HttpResponse('Perfil'), name='perfil_pagina'),
    path('usuarios/', lambda r: HttpResponse('Usuarios'), name='usuario'),
    
    # MARCAS
    path('marcas/', mar_views.lista_marcas, name='lista_marcas'), # type: ignore
    path('marcas/crear/', mar_views.crear_marca, name='crear_marca'), # type: ignore
    path('marcas/editar/<str:codigo_marca>/', mar_views.editar_marca, name='editar_marca'), # type: ignore
    path('marcas/eliminar/<str:codigo_marca>/', mar_views.eliminar_marca, name='eliminar_marca'), # type: ignore
    
    #PRODUCTOS
    path('',                    prod_views.lista_productos,   name='lista_productos'),
    path('crear/',               prod_views.crear_producto,    name='crear_producto'),
    path('buscar/',              prod_views.buscar_producto,   name='buscar_producto'),
    path('producto/<int:pk>/',   prod_views.producto_detalle,  name='producto_detalle'),
    path('producto/<int:pk>/editar/', prod_views.producto_editar, name='producto_editar'),  # faltaba
    path('registro/',            prod_views.producto_registro, name='producto_registro'),
    path('stock-status/',        prod_views.stock_status,      name='stock_status'),

    # Presentaciones
    path('presentacion/<int:producto_pk>/crear/', pres_views.presentacion_crear, name='presentacion_crear'),
    path('presentacion/<int:pk>/editar/', pres_views.presentacion_editar, name='presentacion_editar'),
    path('presentacion/<int:pk>/toggle/', pres_views.presentacion_toggle_activo, name='presentacion_toggle_activo'),
    
    # LOTES
    path('', lot_views.gestion_stock, name='gestion_stock'),
    path('lista/', lot_views.lote_list, name='lote_list'),
    path('crear/', lot_views.lote_create, name='lote_create'),
    path('<str:numero_lote>/', lot_views.lote_detail, name='lote_detail'),
    path('<str:numero_lote>/editar/', lot_views.lote_update, name='lote_update'),
    path('<str:numero_lote>/ajustar-stock/', lot_views.lote_ajustar_stock, name='lote_ajustar_stock'),
    
    # DETALLE PRODUCTO
    path('', deta_views.detalle_producto_lista, name='lista'),
    path('crear/<int:producto_pk>/', deta_views.detalle_producto_crear, name='crear'),
    path('editar/<int:pk>/', deta_views.detalle_producto_editar, name='editar'),
    path('guardar-codigo/<int:pk>/', deta_views.guardar_codigo, name='guardar_codigo'),
]
