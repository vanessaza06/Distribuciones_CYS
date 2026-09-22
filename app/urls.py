from django.urls import path
from django.shortcuts import render
from app.views.categorias import views as cat_views
from app.views.proveedores import views as prov_views
from app.views.marcas import views as mar_views  # type: ignore
from app.views.productos import views as prod_views
from app.views.presentaciones import views as pres_views
from app.views.lotes import views as lot_views
from app.views.detalle_producto import views as deta_views
from app.views.compra import views as compra_views
from app.views.devoluciones import views as dev_views
from app.views.bodega import views as bod_views
from app.views.principal import views as principal_views
from app.views.ventas import views as ventas_views
from app.views.reportes import views as rep_views
from app.views.configuracion import views as config_views


urlpatterns = [
    path("", principal_views.principal, name="principal"),

    # VENTAS
    path("ventas/", ventas_views.ventas, name="ventas"),
    path("ventas/lista/", ventas_views.ventas_lista, name="ventas_lista"),
    path("ventas/punto-venta/", ventas_views.ventas, name="punto_venta"),
    path("ventas/nueva/", ventas_views.nueva_venta, name="nueva_venta"),
    path("ventas/eliminar/<int:pk>/", ventas_views.eliminar_venta, name="eliminar_venta"),
    path("ventas/producto-stock/<int:pk>/", ventas_views.producto_stock_json, name="producto_stock_json"),

    # DEVOLUCIONES
    path("devoluciones/", dev_views.lista_devoluciones, name="lista_devoluciones"),
    path("devoluciones/buscar/",dev_views.buscar_venta_devolucion,name="buscar_venta_devolucion",),
    path("devoluciones/venta/<int:venta_id>/",dev_views.seleccionar_venta_devolucion,name="seleccionar_venta_devolucion", ),
    path( "devoluciones/venta/<int:venta_id>/registrar/",dev_views.registrar_devolucion,name="registrar_devolucion",),
    path( "devoluciones/detalle/<int:venta_id>/",dev_views.detalle_venta_devolucion,name="detalle_venta_devolucion",),
    path("devoluciones/comprobante/<int:pk>/",dev_views.comprobante_devolucion,name="comprobante_devolucion",),
    path("devoluciones/<int:pk>/", dev_views.detalle_devolucion, name="detalle_devolucion",),
    path("ventas/dia/", ventas_views.ventas_dia, name="ventas_dia"),
    path("ventas/exportar/excel/", ventas_views.exportar_ventas_excel, name="exportar_ventas_excel"),
    path("ventas/exportar/pdf/", ventas_views.exportar_ventas_pdf, name="exportar_ventas_pdf"),

    # CAJA
    path("ventas/caja/", ventas_views.caja, name="caja"),
    path("ventas/caja/apertura/", ventas_views.apertura_caja, name="apertura_caja"),
    path("ventas/caja/cierre/", ventas_views.cierre_caja, name="cierre_caja"),
    path("ventas/caja/conteo/", ventas_views.registrar_conteo, name="registrar_conteo"),

    


    # CATEGORIAS
    path("categorias/", cat_views.categorias_lista, name="categorias_lista"),
    path("categorias/crear/", cat_views.categoria_crear, name="categoria_crear"),
    path(
        "categorias/editar/<int:pk>/",
        cat_views.categoria_editar,
        name="categoria_editar",
    ),
    path(
        "categorias/toggle/<int:pk>/",
        cat_views.categoria_toggle_activo,
        name="categoria_toggle_activo",
    ),
    # PROVEEDORES
    path("proveedores/", prov_views.lista_proveedores, name="lista_proveedores"),
    path("proveedores/crear/", prov_views.crear_proveedor, name="crear_proveedor"),
    path("proveedores/detalle/<str:id>/",prov_views.detalle_proveedor,name="detalle_proveedor",),
    path("proveedores/editar/<str:id>/",prov_views.editar_proveedor,name="editar_proveedor",),
    path("proveedores/eliminar/<str:id>/",prov_views.eliminar_proveedor,name="eliminar_proveedor",),
    path( "proveedores/activar/<str:id>/", prov_views.activar_proveedor, name="activar_proveedor",),
    path("proveedores/desactivar/<str:id>/",prov_views.desactivar_proveedor,name="desactivar_proveedor",),
    path( "proveedores/sancionar/<str:id>/",prov_views.sancionar_proveedor, name="sancionar_proveedor",),
    path("proveedores/levantar-sancion/<str:id>/",prov_views.levantar_sancion_proveedor, name="levantar_sancion_proveedor",),
    # Modales / AJAX Proveedores
    path("proveedores/modal/detalle/<str:id>/",prov_views.detalle_proveedor_modal,name="detalle_proveedor_modal",),
    path("proveedores/modal/desactivar/<str:id>/",prov_views.desactivar_proveedor_modal,name="desactivar_proveedor_modal",),
    path("proveedores/modal/reactivar/<str:id>/",prov_views.reactivar_proveedor_modal,name="reactivar_proveedor_modal",),
    path("proveedores/modal/sancionar/<str:id>/",prov_views.sancionar_proveedor_modal,name="sancionar_proveedor_modal",),

    # MARCAS
    path("marcas/", mar_views.lista_marcas, name="lista_marcas"),  # type: ignore
    path("marcas/crear/", mar_views.crear_marca, name="crear_marca"),  # type: ignore
    path("marcas/editar/<str:codigo_marca>/", mar_views.editar_marca, name="editar_marca"),  # type: ignore
    path("marcas/eliminar/<str:codigo_marca>/", mar_views.eliminar_marca, name="eliminar_marca"),  # type: ignore

    # PRODUCTOS
    path("productos/", prod_views.lista_productos, name="lista_productos"),
    path("crear-producto/", prod_views.crear_producto, name="crear_producto"),
    path("buscar/", prod_views.buscar_producto, name="buscar_producto"),
    path("producto/<int:pk>/", prod_views.producto_detalle, name="producto_detalle"),
    path(
        "producto/<int:pk>/editar/", prod_views.producto_editar, name="producto_editar"
    ),
    path("registro/", prod_views.producto_registro, name="producto_registro"),
    path("stock-status/", prod_views.stock_status, name="stock_status"),
    path(
        "producto/<int:pk>/toggle/",
        prod_views.producto_toggle_activo,
        name="producto_toggle_activo",
    ),

        # PRESENTACIONES
path("presentaciones/", pres_views.presentacion_lista, name="presentacion_lista"),
path(
    "presentacion/<int:producto_pk>/crear/",
    pres_views.presentacion_crear,
    name="presentacion_crear",
),
path(
    "presentacion/<int:pk>/editar/",
    pres_views.presentacion_editar,
    name="presentacion_editar",
),
path(
    "presentacion/<int:pk>/toggle/",
    pres_views.presentacion_toggle_activo,
    name="presentacion_toggle_activo",
),
        # COMPRAS
    path("compras/", compra_views.lista_compras, name="lista_compras"),
    path("compras/<int:id>/", compra_views.detalle_compra, name="detalle_compra",),
    path("compras/estado/",compra_views.cambiar_estado_compra, name="cambiar_estado_compra", ),
    path("compras/estado/<int:id>/",compra_views.cambiar_estado_compra,name="cambiar_estado_compra_id",),
    path("compras/pago/",compra_views.registrar_pago_compra,name="registrar_pago_compra",),
    path("compras/pago/<int:id>/",compra_views.registrar_pago_compra,name="registrar_pago_compra_id",),

    # LOTES
    path("lotes/", lot_views.gestion_stock, name="gestion_stock"),
    path("lotes/lista/", lot_views.lote_list, name="lote_list"),
    path("lotes/crear/", lot_views.lote_create, name="lote_create"),
    path("lotes/<str:numero_lote>/", lot_views.lote_detail, name="lote_detail"),
    path("lotes/<str:numero_lote>/editar/", lot_views.lote_update, name="lote_update"),
    path(
        "lotes/<str:numero_lote>/ajustar-stock/",
        lot_views.lote_ajustar_stock,
        name="lote_ajustar_stock",
    ),

    # DETALLE PRODUCTO
    path(
        "detalle-producto/",
        deta_views.detalle_producto_lista,
        name="detalle_producto_lista",
    ),
    path(
        "detalle-producto/crear/<int:producto_pk>/",
        deta_views.detalle_producto_crear,
        name="detalle_producto_crear",
    ),
    path(
        "detalle-producto/editar/<int:pk>/",
        deta_views.detalle_producto_editar,
        name="detalle_producto_editar",
    ),
    path(
        "detalle-producto/guardar-codigo/<int:pk>/",
        deta_views.guardar_codigo,
        name="guardar_codigo",
    ),
    path("detalle/<int:producto_pk>/crear-rapido/", deta_views.detalle_producto_crear_rapido, name="detalle_producto_crear_rapido"),
    # BODEGA
    path("bodega/", bod_views.bodega_home, name="bodega_home"),
    path("bodega/agenda/", bod_views.agenda_list, name="agenda_list"),
    path("bodega/agenda/nueva/", bod_views.agenda_create, name="agenda_create"),
    path("bodega/agenda/<int:codigo>/", bod_views.agenda_detail, name="agenda_detail"),
    path(
        "bodega/agenda/<int:codigo>/editar/",
        bod_views.agenda_update,
        name="agenda_update",
    ),
    path(
        "bodega/agenda/<int:codigo>/completar/",
        bod_views.agenda_completar,
        name="agenda_completar",
    ),
    path(
        "bodega/agenda/<int:codigo_agenda>/hallazgo/",
        bod_views.hallazgo_create,
        name="hallazgo_create",
    ),
    path("bodega/hallazgos/", bod_views.hallazgo_list, name="hallazgo_list"),
    path(
        "bodega/ajustar-stock/<int:pk>/", bod_views.ajustar_stock, name="ajustar_stock"
    ),

    # REPORTES
    path("reportes/", rep_views.reportes_home, name="reportes_home"),  # type: ignore
    path("reportes/ventas/", rep_views.reporte_ventas, name="reporte_ventas"),  # type: ignore
    path("reportes/compras/", rep_views.reporte_compras, name="reporte_compras"),
    path("reportes/inventario/", rep_views.reporte_inventario, name="reporte_inventario"),
    path("reportes/stock-bajo/", rep_views.reporte_stock_bajo, name="reporte_stock_bajo"),
    path("reportes/proveedores/", rep_views.reporte_proveedores, name="reporte_proveedores"),
    path("reportes/exportar/<str:tipo>/", rep_views.reporte_exportar, name="reporte_exportar"),

    # CONFIGURACION
    path("configuracion/", config_views.index, name="configuracion_index"),
    path("configuracion/empresa/", config_views.guardar_empresa, name="guardar_empresa"),
    path("configuracion/empresa/verificar/", config_views.verificar_clave_empresa, name="verificar_clave_empresa"),
    path("configuracion/empresa/bloquear/", config_views.bloquear_empresa, name="bloquear_empresa"),
    path("configuracion/impuestos/", config_views.guardar_impuestos, name="guardar_impuestos"),
    path("configuracion/backup/", config_views.crear_backup, name="crear_backup"),
]
