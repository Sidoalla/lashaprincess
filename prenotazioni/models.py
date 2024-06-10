# prenotazioni/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Prenotazione(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    data_prenotazione = models.DateField()
    ora_prenotazione = models.TimeField()
    tipo = models.CharField(max_length=100)
    email_consent = models.BooleanField(default=False)
    consent_timestamp = models.DateTimeField(null=True, blank=True)
    cancellato = models.BooleanField(default=False)
    motivo_cancellazione = models.CharField(max_length=255, null=True, blank=True)
    google_calendar_event_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'{self.nome} - {self.data_prenotazione} {self.ora_prenotazione}'


class ClienteAppunti(models.Model):
    prenotazione = models.ForeignKey(Prenotazione, on_delete=models.CASCADE)
    appunto = models.TextField()
    data_creazione = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Appunti per {self.prenotazione.nome} - {self.data_creazione}"

    class Meta:
        permissions = [
            ("can_edit_prenotazione", "Can edit prenotazione"),
            ("can_delete_prenotazione", "Can delete prenotazione"),
        ]
