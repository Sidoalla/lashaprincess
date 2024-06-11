from django.contrib import admin
from django.urls import path, include
from prenotazioni.views import webhook_notification  # Importa la funzione del webhook

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('prenotazioni.urls')),
    path('webhook_notification/', webhook_notification, name='webhook_notification'),  # Aggiungi questa linea
]
