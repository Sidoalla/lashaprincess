from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.select_artist, name='select_artist'),  # Pagina di selezione
    path('home/', views.home, name='home'),  # Pagina del calendario
    path('get_events/', views.get_events, name='get_events'),
    path('aggiungi_prenotazione/', views.aggiungi_prenotazione, name='aggiungi_prenotazione'),
    path('informativa-privacy/', views.informativa_privacy, name='informativa_privacy'),
    path('lista_prenotazioni/', views.lista_prenotazioni, name='lista_prenotazioni'),
    path('modifica_prenotazione/<int:prenotazione_id>/', views.modifica_prenotazione, name='modifica_prenotazione'),
    path('cancella_prenotazione/<int:prenotazione_id>/', views.cancella_prenotazione, name='cancella_prenotazione'),
    path('is_admin/', views.is_admin, name='is_admin'),
    path('login/', auth_views.LoginView.as_view(template_name='prenotazioni/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
   # path('aggiungi_appunto/', views.aggiungi_appunto, name='aggiungi_appunto'),
]
