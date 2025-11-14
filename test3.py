import requests

# Login
login_response = requests.post('http://localhost:8000/api/auth/login/', json={
    'username': 'Fer', 'password': 'Espol123'
})
token = login_response.json()['access']

# 1. Subir archivo (se transcribe y resume automáticamente)
with open('./economía.mp3', 'rb') as audio_file:
    response = requests.post(
        'http://localhost:8000/api/transcriptions/upload/',
        headers={'Authorization': f'Bearer {token}'},
        files={'audio_file': audio_file}
    )

transcription_id = response.json()['id']

# # 2. Monitorear progreso
# summary_status = requests.get(
#     f'http://localhost:8000/api/transcriptions/{transcription_id}/summary/',
#     headers={'Authorization': f'Bearer {token}'}
# )
# print(summary_status.json())

# 3. Solicitar resumen personalizado
custom_summary = requests.post(
    f'http://localhost:8000/api/transcriptions/{8}/summary/',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'prompt': 'Genere un resumen extenso y detallado, destacando los puntos clave y proporcionando contexto',
        'force': True  # Regenerar si ya existe
    }
)
print(custom_summary.json())