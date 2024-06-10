from django.contrib import admin
from .models import Prenotazione

@admin.register(Prenotazione)
class PrenotazioneAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'data_prenotazione', 'ora_prenotazione', 'email_consent', 'consent_timestamp')
    list_filter = ('email_consent', 'data_prenotazione')
    search_fields = ('nome', 'email')
