import logging
import json
from datetime import datetime, timedelta
from django.utils import timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, permission_required
from .models import Prenotazione
from dotenv import load_dotenv
import os

load_dotenv()

# Leggi le credenziali dal contenuto JSON delle variabili d'ambiente
GOOGLE_CALENDAR_SERVICE_ACCOUNT_INFO = json.loads(os.getenv('GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE'))
GOOGLE_SHEETS_SERVICE_ACCOUNT_INFO = json.loads(os.getenv('GOOGLE_SHEETS_SERVICE_ACCOUNT_FILE'))
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/spreadsheets']
CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID')
SHEET_ID = os.getenv('GOOGLE_SHEET_ID')

# Configura il logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Funzione per selezionare l'artista
def select_artist(request):
    return render(request, 'prenotazioni/select_artist.html')

# Funzione per la home
def home(request):
    is_admin = request.user.is_authenticated and request.user.is_staff
    return render(request, 'prenotazioni/index.html', {'is_admin': is_admin})

# Funzione per verificare se l'utente è admin
def is_admin(request):
    is_admin = request.user.is_authenticated and request.user.is_staff
    return JsonResponse({'is_admin': is_admin})

# Funzione per ottenere gli eventi
def get_events(request):
    date = request.GET.get('date')
    if date:
        events = Prenotazione.objects.filter(data_prenotazione=date, cancellato=False).values('id', 'nome', 'email', 'data_prenotazione', 'ora_prenotazione', 'tipo')
    else:
        events = Prenotazione.objects.filter(cancellato=False).values('id', 'nome', 'email', 'data_prenotazione', 'ora_prenotazione', 'tipo')
    events_list = []
    for event in events:
        events_list.append({
            'id': event['id'],
            'title': f"{event['nome']} ({event['tipo']})",
            'start': f"{event['data_prenotazione']}T{event['ora_prenotazione']}"
        })
    return JsonResponse(events_list, safe=False)

@csrf_exempt
def aggiungi_prenotazione(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.debug(f'Dati ricevuti: {data}')
            nome = data.get('nome')
            email = data.get('email')
            data_prenotazione = data.get('data_prenotazione')
            ora_prenotazione = data.get('ora_prenotazione')
            tipo = data.get('tipo')
            email_consent = data.get('email_consent', False)
            consent_timestamp = timezone.now() if email_consent else None

            if not all([nome, email, data_prenotazione, ora_prenotazione, tipo]):
                return JsonResponse({'status': 'error', 'message': 'Tutti i campi sono obbligatori.'}, status=400)

            ora_prenotazione = datetime.strptime(ora_prenotazione, "%H:%M").strftime("%H:%M")

            prenotazioni_sovrapposte = Prenotazione.objects.filter(data_prenotazione=data_prenotazione, ora_prenotazione=ora_prenotazione, cancellato=False).exists()
            if prenotazioni_sovrapposte:
                logger.debug(f'Prenotazione sovrapposta trovata per {data_prenotazione} alle {ora_prenotazione}')
                return JsonResponse({'status': 'error', 'message': "L'orario selezionato è già prenotato. Scegli un altro orario."}, status=400)

            prenotazione = Prenotazione(
                nome=nome,
                email=email,
                data_prenotazione=data_prenotazione,
                ora_prenotazione=ora_prenotazione,
                tipo=tipo,
                email_consent=email_consent,
                consent_timestamp=consent_timestamp
            )

            prenotazione.save()

            try:
                event_id = add_event_to_google_calendar(prenotazione)
                prenotazione.google_calendar_event_id = event_id
                prenotazione.save()
            except Exception as e:
                logger.error(f"Errore durante l'aggiunta dell'evento a Google Calendar: {e}")
                return JsonResponse({'status': 'error', 'message': 'Errore durante l\'aggiunta dell\'evento a Google Calendar.'}, status=500)

            try:
                add_booking_to_google_sheets(prenotazione)
            except Exception as e:
                logger.error(f"Errore durante l'aggiunta della prenotazione a Google Sheets: {e}")
                return JsonResponse({'status': 'error', 'message': 'Errore durante l\'aggiunta della prenotazione a Google Sheets.'}, status=500)

            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(f"Errore durante l'aggiunta della prenotazione: {e}")
            return JsonResponse({'status': 'error', 'message': 'Errore durante l\'aggiunta della prenotazione.'}, status=500)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def informativa_privacy(request):
    return render(request, 'prenotazioni/informativa_privacy.html')

def add_event_to_google_calendar(prenotazione):
    credentials = service_account.Credentials.from_service_account_info(
        GOOGLE_CALENDAR_SERVICE_ACCOUNT_INFO, scopes=['https://www.googleapis.com/auth/calendar'])
    service = build('calendar', 'v3', credentials=credentials)

    start_time = datetime.strptime(prenotazione.ora_prenotazione, "%H:%M").strftime("%H:%M:%S")
    end_time = (datetime.strptime(start_time, "%H:%M:%S") + timedelta(hours=1)).strftime("%H:%M:%S")

    event = {
        'summary': f'Prenotazione di {prenotazione.nome} ({prenotazione.tipo})',
        'description': f'Email: {prenotazione.email}\nTipo: {prenotazione.tipo}',
        'start': {
            'dateTime': f'{prenotazione.data_prenotazione}T{start_time}',
            'timeZone': 'Europe/Rome',
        },
        'end': {
            'dateTime': f'{prenotazione.data_prenotazione}T{end_time}',
            'timeZone': 'Europe/Rome',
        }
    }
    try:
        event_result = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        logger.info(f'Evento aggiunto a Google Calendar: {event["summary"]}')
        return event_result['id']
    except Exception as e:
        logger.error(f"Errore durante l'aggiunta dell'evento a Google Calendar: {e}")
        raise

def format_time(time_str):
    try:
        # Prova a formattare l'orario nel formato "HH:MM"
        time_obj = datetime.strptime(time_str, "%H:%M")
        return time_obj.strftime("%H:%M")
    except ValueError:
        try:
            # Prova a formattare l'orario nel formato "HH:MM AM/PM"
            time_obj = datetime.strptime(time_str, "%I:%M %p")
            return time_obj.strftime("%H:%M")
        except ValueError:
            # Gestione degli errori di conversione
            return time_str

def format_column_times():
    credentials = service_account.Credentials.from_service_account_info(
        GOOGLE_SHEETS_SERVICE_ACCOUNT_INFO, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()

    try:
        # Recupera i dati esistenti
        result = sheet.values().get(spreadsheetId=SHEET_ID, range='Sheet1!D2:D').execute()
        values = result.get('values', [])

        # Format tutta la colonna
        for row in values:
            row[0] = format_time(row[0])

        # Aggiorna i dati formattati su Google Sheets
        body = {
            'values': values
        }

        result = sheet.values().update(
            spreadsheetId=SHEET_ID,
            range='Sheet1!D2:D',
            valueInputOption='RAW',
            body=body
        ).execute()
        print(f'Orari aggiornati su Google Sheets: {result}')

    except Exception as e:
        print(f"Errore durante l'aggiornamento degli orari su Google Sheets: {e}")
        raise

# Chiama questa funzione per formattare la colonna degli orari
format_column_times()

def add_booking_to_google_sheets(prenotazione):
    credentials = service_account.Credentials.from_service_account_info(
        GOOGLE_SHEETS_SERVICE_ACCOUNT_INFO, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()

    # Formatta l'orario prima di inviarlo a Google Sheets
    ora_prenotazione_formattata = format_time(prenotazione.ora_prenotazione)

    values = [
        [prenotazione.nome, prenotazione.email, prenotazione.data_prenotazione, ora_prenotazione_formattata, prenotazione.tipo, prenotazione.consent_timestamp.isoformat() if prenotazione.consent_timestamp else '', '', '']
    ]
    body = {
        'values': values
    }

    if not SHEET_ID:
        logger.error('SHEET_ID non impostato')
        raise ValueError('SHEET_ID non impostato')

    try:
        result = sheet.values().append(
            spreadsheetId=SHEET_ID,
            range='Sheet1!A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        logger.info(f'Prenotazione aggiunta a Google Sheets: {result}')
    except Exception as e:
        logger.error(f"Errore durante l'aggiunta della prenotazione a Google Sheets: {e}")
        raise

@csrf_exempt
def webhook_notification(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            event_id = data['id']

            if 'resourceState' in data and data['resourceState'] == 'deleted':
                # L'evento è stato eliminato, cancella la prenotazione corrispondente
                try:
                    prenotazione = Prenotazione.objects.get(google_calendar_event_id=event_id)
                    prenotazione.cancellato = True
                    prenotazione.save()
                    logger.info(f'Prenotazione cancellata per l\'evento Google Calendar ID: {event_id}')
                except Prenotazione.DoesNotExist:
                    logger.error(f'Prenotazione non trovata per l\'evento Google Calendar ID: {event_id}')
            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(f"Errore durante la gestione della notifica webhook: {e}")
            return JsonResponse({'status': 'error', 'message': 'Errore durante la gestione della notifica webhook.'}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
@login_required
@permission_required('prenotazioni.delete_prenotazione', raise_exception=True)
def cancella_prenotazione(request, prenotazione_id):
    if request.method == 'POST':
        motivo = json.loads(request.body).get('motivo')
        try:
            prenotazione = Prenotazione.objects.get(id=prenotazione_id)
            prenotazione.cancellato = True
            prenotazione.motivo_cancellazione = motivo
            prenotazione.save()

            # Cancella evento da Google Calendar e Google Sheets
            try:
                delete_event_from_google_calendar(prenotazione)
            except Exception as e:
                logger.error(f"Errore durante la rimozione dell'evento da Google Calendar: {e}")

            try:
                add_cancellation_reason_to_google_sheets(prenotazione, motivo)
            except Exception as e:
                logger.error(f"Errore durante l'aggiunta del motivo della cancellazione a Google Sheets: {e}")

            return JsonResponse({'status': 'success'})
        except Prenotazione.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Prenotazione non trovata.'}, status=404)
        except Exception as e:
            logger.error(f"Errore durante la cancellazione della prenotazione: {e}")
            return JsonResponse({'status': 'error', 'message': 'Errore durante la cancellazione della prenotazione.'}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def delete_event_from_google_calendar(prenotazione):
    credentials = service_account.Credentials.from_service_account_info(
        GOOGLE_CALENDAR_SERVICE_ACCOUNT_INFO, scopes=['https://www.googleapis.com/auth/calendar'])
    service = build('calendar', 'v3', credentials=credentials)

    try:
        if prenotazione.google_calendar_event_id:
            service.events().delete(calendarId=CALENDAR_ID, eventId=prenotazione.google_calendar_event_id).execute()
            logger.info(f'Evento rimosso da Google Calendar: {prenotazione.google_calendar_event_id}')
        else:
            logger.error('ID evento Google Calendar non trovato per la prenotazione.')
            raise ValueError('ID evento Google Calendar non trovato')
    except Exception as e:
        logger.error(f"Errore durante la rimozione dell'evento da Google Calendar: {e}")
        raise

def add_cancellation_reason_to_google_sheets(prenotazione, motivo):
    credentials = service_account.Credentials.from_service_account_info(
        GOOGLE_SHEETS_SERVICE_ACCOUNT_INFO, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()

    try:
        result = sheet.values().get(spreadsheetId=SHEET_ID, range='Sheet1!A1:H').execute()
        values = result.get('values', [])

        logger.debug(f'Valori attuali nel foglio: {values}')

        # Formatta la data e l'ora della prenotazione
        data_prenotazione_str = str(prenotazione.data_prenotazione)
        ora_prenotazione_str = prenotazione.ora_prenotazione.strftime("%H:%M")  # Usa strftime per convertire datetime.time in stringa

        # Trova la riga da aggiornare
        row_found = False
        for i, row in enumerate(values):
            logger.debug(f'Confrontando riga: {row}')
            sheet_time = row[3]  # Usa direttamente la cella della colonna D senza subscript

            logger.debug(f'Confrontando ora: {sheet_time} con {ora_prenotazione_str}')

            if (
                row[0].strip().lower() == prenotazione.nome.strip().lower() and
                row[1].strip().lower() == prenotazione.email.strip().lower() and
                row[2] == data_prenotazione_str and
                sheet_time == ora_prenotazione_str
            ):
                # Assicurati che la riga abbia abbastanza colonne
                while len(row) < 8:
                    row.append('')
                row[6] = 'Cancellato'  # Assicurarsi che la colonna 6 sia 'Stato'
                row[7] = motivo  # Assicurarsi che la colonna 7 sia 'Motivo Cancellazione'
                row_found = True
                logger.debug(f'Riga trovata per aggiornamento: {row}')
                break

        if not row_found:
            logger.error(f'Riga non trovata per la prenotazione: {prenotazione.nome}, {prenotazione.email}, {prenotazione.data_prenotazione}, {prenotazione.ora_prenotazione}')
            return

        # Aggiorna la riga specifica
        range_to_update = f'Sheet1!A{i+1}:H{i+1}'  # i+1 perché l'indice di riga nell'intervallo inizia da 1
        body = {
            'values': [values[i]]
        }

        if not SHEET_ID:
            logger.error('SHEET_ID non impostato')
            raise ValueError('SHEET_ID non impostato')

        result = sheet.values().update(
            spreadsheetId=SHEET_ID,
            range=range_to_update,
            valueInputOption='RAW',
            body=body
        ).execute()
        logger.info(f'Motivo della cancellazione aggiornato su Google Sheets: {result}')

    except Exception as e:
        logger.error(f"Errore durante l'aggiunta del motivo della cancellazione a Google Sheets: {e}")
        raise


@login_required
@permission_required('prenotazioni.change_prenotazione', raise_exception=True)
@csrf_exempt
def modifica_prenotazione(request, prenotazione_id):
    if request.method == 'POST':
        prenotazione = get_object_or_404(Prenotazione, id=prenotazione_id)
        data = json.loads(request.body)
        prenotazione.data_prenotazione = data.get('data_prenotazione', prenotazione.data_prenotazione)
        prenotazione.ora_prenotazione = data.get('ora_prenotazione', prenotazione.ora_prenotazione)
        prenotazione.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def lista_prenotazioni(request):
    prenotazioni = Prenotazione.objects.all()
    return render(request, 'prenotazioni/lista_prenotazioni.html', {'prenotazioni': prenotazioni})
