from django.urls import path,include
from app.views import *

urlpatterns = [
    # Definirás tus urls aquí, por ejemplo:
    # path('', views.home, name='home'),
    path('bodega/', include('app.views.bodega.urls'))
  
]
