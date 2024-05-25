from django.urls import path
from . import views

urlpatterns = [
    path('get_events/', views.get_events, name='get_events'),
    path('aggiungi_prenotazione/', views.aggiungi_prenotazione, name='aggiungi_prenotazione'),
    path('', views.home, name='home'),
]
