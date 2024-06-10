from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('prenotazioni.urls')),  # Questo include le URL del modulo prenotazioni
]
