from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json

def home(request):
    return render(request, 'prenotazioni/index.html')

def get_events(request):
    events = []  # Replace with your actual events
    return JsonResponse(events, safe=False)

@csrf_exempt
def aggiungi_prenotazione(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        nome = data.get('nome')
        email = data.get('email')
        data_prenotazione = data.get('data_prenotazione')
        ora_prenotazione = data.get('ora_prenotazione')
        # Add logic to save the booking
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Invalid request'}, status=400)
