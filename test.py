import requests
# Login para obtener token
login_response = requests.post('http://localhost:8000/api/auth/login/', json={
    'username': 'Fer',
    'password': 'Espol123'
})
token = login_response.json()['access']


# response = requests.post(
#         'http://localhost:8000/api/transcriptions/5/transcribe/',
#         headers={'Authorization': f'Bearer {token}'},
#         json={"force": False, "model": "medium", "language": "es"}
#     )







with open('./Diseno.mp3', 'rb') as audio_file:
    response = requests.post(
        'http://localhost:8000/api/transcriptions/upload/',
        headers={'Authorization': f'Bearer {token}'},
        files={'audio_file': audio_file},
        data={'language': 'Spanish'}
    )


print(response.json())
