import json

# Percorsi dei file JSON
calendar_file_path = '/Users/alessiocavatassi/Desktop/SITO SIDOLA/credentials/dev-dispatch-424612-f2-f24cba7a8111.json'
sheets_file_path = '/Users/alessiocavatassi/Desktop/SITO SIDOLA/credentials/dev-dispatch-424612-f2-775a09811298.json'

# Funzione per testare la validità del file JSON
def test_json_file(file_path):
    try:
        with open(file_path) as f:
            data = json.load(f)
        print(f"File JSON '{file_path}' caricato correttamente")
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Errore nel leggere il file JSON '{file_path}': {e}")

# Testa entrambi i file
test_json_file(calendar_file_path)
test_json_file(sheets_file_path)
