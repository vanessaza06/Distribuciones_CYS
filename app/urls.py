from django.urls import path
from app.views.categorias import views
from app.views.proveedores import views as prov_views
#from app.views.bodega import views 
import app

app_name = 'app'

urlpatterns = [
    # Definirás tus urls aquí, por ejemplo:
    # path('', views.home, name='home'),
   # path('bodega/', include('app.views.bodega.urls')),
 #CATEGORIA 
    path('categorias/', views.categorias_lista, name='categorias_lista'),

    #PROVEEDORES
     path('proveedores/', prov_views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/nuevo/', prov_views.crear_proveedor, name='crear_proveedor'),
    path('proveedores/detalle/<str:id>/', prov_views.detalle_proveedor, name='detalle_proveedor'),
    path('proveedores/editar/<str:id>/', prov_views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<str:id>/', prov_views.eliminar_proveedor, name='eliminar_proveedor'),
    path('proveedores/activar/<str:id>/', prov_views.activar_proveedor, name='activar_proveedor'),
    path('proveedores/desactivar/<str:id>/', prov_views.desactivar_proveedor, name='desactivar_proveedor'),
    path('proveedores/sancionar/<str:id>/', prov_views.sancionar_proveedor, name='sancionar_proveedor'),
    path('proveedores/modal/detalle/<str:id>/', prov_views.detalle_proveedor_modal, name='detalle_proveedor_modal'),
    path('proveedores/modal/desactivar/<str:id>/', prov_views.desactivar_proveedor_modal, name='desactivar_proveedor_modal'),
    path('proveedores/modal/reactivar/<str:id>/', prov_views.reactivar_proveedor_modal, name='reactivar_proveedor_modal'),
    path('proveedores/modal/sancionar/<str:id>/', prov_views.sancionar_proveedor_modal, name='sancionar_proveedor_modal'),
    path('proveedores/modal/levantar-sancion/<str:id>/', prov_views.levantar_sancion_proveedor, name='levantar_sancion_proveedor'),
]


