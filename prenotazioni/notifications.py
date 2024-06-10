import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Prenotazione  # Il modello Prenotazione del tuo sito

@csrf_exempt
def notifications(request):
    if request.method == 'POST':
        notification = json.loads(request.body.decode('utf-8'))
        if notification['resourceState'] == 'deleted':
            event_id = notification['resourceId']
            handle_event_deletion(event_id)
    return HttpResponse(status=200)

def handle_event_deletion(event_id):
    # Logica per gestire l'eliminazione dell'evento
    Prenotazione.objects.filter(google_calendar_event_id=event_id).delete()
