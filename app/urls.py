from django.urls import path
from app.views.categorias import views
from app.views.bodega import views 
import app

app_name = 'app'

urlpatterns = [
    # Definirás tus urls aquí, por ejemplo:
    # path('', views.home, name='home'),
   # path('bodega/', include('app.views.bodega.urls')),
   # path('proveedores/', include('app.views.proveedores.urls')),
    #path('devoluciones/', include('app.views.devoluciones.urls')),
   # path('compra/', include('app.views.compra.urls')),
    path('categorias/', views.categorias_lista, name='categorias_lista'),
