from django import forms
from .models import Prenotazione

class PrenotazioneForm(forms.ModelForm):
    class Meta:
        model = Prenotazione
        fields = ['nome', 'email', 'data_prenotazione', 'ora_prenotazione', 'email_consent']
