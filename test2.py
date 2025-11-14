import requests
import redis

# Conectar a Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Login
login_response = requests.post('http://localhost:8000/api/auth/login/', json={
    'username': 'Fer', 'password': 'Espol123'
})
token = login_response.json()['access']

print("📊 Estado inicial de Redis:")
print(f"  - Cola celery: {r.llen('celery')} tareas")

# Ver todas las keys antes
keys_before = r.keys("*")
print(f"  - Total keys: {len(keys_before)}")

# Upload file
print("\n📤 Uploading file...")
with open('./Diseno.mp3', 'rb') as audio_file:
    response = requests.post(
        'http://localhost:8000/api/transcriptions/upload/',
        headers={'Authorization': f'Bearer {token}'},
        files={'audio_file': audio_file},
        data={'language': 'Spanish'}
    )

print(f"📨 Upload response: {response.status_code}")
response_data = response.json()
print(f"📨 Response data: {response_data}")

# Ver estado después
print(f"\n📊 Estado después del upload:")
print(f"  - Cola celery: {r.llen('celery')} tareas")

# Ver nuevas keys
keys_after = r.keys("*")
new_keys = set(keys_after) - set(keys_before)
if new_keys:
    print(f"🆕 Nuevas keys creadas: {len(new_keys)}")
    for key in new_keys:
        print(f"  - {key.decode()}")
else:
    print("❌ No se crearon nuevas keys")

# Ver contenido de la cola si hay algo
queue_length = r.llen('celery')
if queue_length > 0:
    print(f"\n📋 Tareas en cola ({queue_length}):")
    tasks = r.lrange('celery', 0, queue_length-1)
    for i, task in enumerate(tasks):
        print(f"  {i+1}. {task[:150]}...")