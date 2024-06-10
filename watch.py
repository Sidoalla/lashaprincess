import google.auth
from googleapiclient.discovery import build

def watch_calendar():
    credentials, project = google.auth.default()
    service = build('calendar', 'v3', credentials=credentials)

    body = {
        'id': 'unique-channel-id',  # ID univoco per identificare il canale
        'type': 'web_hook',
        'address': 'https://your-server.com/notifications/',  # Endpoint che riceve le notifiche
        'params': {
            'ttl': '3600'
        }
    }

    response = service.events().watch(calendarId='primary', body=body).execute()
    print(response)

if __name__ == "__main__":
    watch_calendar()
