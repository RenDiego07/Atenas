"""
Test script for simplified API with only 2 endpoints:
1. POST /api/transcriptions/upload/
2. GET /api/transcriptions/
"""
import requests
import time

BASE_URL = 'http://localhost:8000/api'

# ============================================================================
# 1. LOGIN
# ============================================================================
print("🔐 Logging in...")
login_response = requests.post(f'{BASE_URL}/auth/login/', json={
    'username': 'Fer',
    'password': 'Espol123'
})

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.text}")
    exit(1)

token = login_response.json()['access']
headers = {'Authorization': f'Bearer {token}'}
print("✅ Login successful\n")

# ============================================================================
# 2. UPLOAD AUDIO WITH CUSTOM PROMPT
# ============================================================================
print("📤 Uploading audio with custom prompt...")
with open('./economía.mp3', 'rb') as audio_file:
    response = requests.post(
        f'{BASE_URL}/transcriptions/upload/',
        headers=headers,
        files={'audio_file': audio_file},
        data={
            'custom_prompt': 'Resume los puntos clave y conceptos importantes del audio, enfocándote en datos económicos y tendencias financieras.'
        }
    )

if response.status_code != 201:
    print(f"❌ Upload failed: {response.text}")
    exit(1)

upload_data = response.json()
transcription_id = upload_data['id']
print(f"✅ Upload exitoso - ID: {transcription_id}")
print(f"   📊 Status: {upload_data['status']}")
print(f"   🎵 Audio: {upload_data.get('audio_name', 'N/A')}")
print(f"   📝 Summary: {upload_data.get('summary_content', 'Procesando...')}")
print("🤖 Pipeline automático iniciado\n")

# ============================================================================
# 3. WAIT FOR PROCESSING (opcional - solo para demo)
# ============================================================================
print("⏳ Esperando a que termine el procesamiento (esto puede tomar varios minutos)...")
print("   Puedes cancelar con Ctrl+C y consultar el historial más tarde\n")

# Descomentar para esperar el procesamiento completo
# max_wait = 300  # 5 minutos
# interval = 10   # Consultar cada 10 segundos
# 
# for i in range(0, max_wait, interval):
#     time.sleep(interval)
#     
#     # Consultar historial
#     history_response = requests.get(f'{BASE_URL}/transcriptions/', headers=headers)
#     transcriptions = history_response.json()
#     
#     # Buscar nuestra transcripción
#     current = next((t for t in transcriptions if t['id'] == transcription_id), None)
#     
#     if current:
#         print(f"   [{i}s] Status: {current['status']}")
#         
#         if current['status'] == 'done' and current['summary_content']:
#             print("✅ Procesamiento completado!\n")
#             break
#     
#     if i >= max_wait - interval:
#         print("⚠️  Tiempo de espera agotado. Consulta el historial más tarde.")

# ============================================================================
# 4. GET HISTORY (Endpoint principal para el frontend)
# ============================================================================
print("📋 Consultando historial de transcripciones...")
history_response = requests.get(f'{BASE_URL}/transcriptions/', headers=headers)

if history_response.status_code != 200:
    print(f"❌ Error getting history: {history_response.text}")
    exit(1)

transcriptions = history_response.json()
print(f"✅ Total de transcripciones: {len(transcriptions)}\n")

# ============================================================================
# 5. DISPLAY HISTORY FORMAT
# ============================================================================
print("=" * 80)
print("📚 HISTORIAL DE TRANSCRIPCIONES")
print("=" * 80)

for idx, t in enumerate(transcriptions[:5], 1):  # Mostrar últimas 5
    print(f"\n{idx}. Transcripción #{t['id']}")
    print(f"   🎵 Audio: {t.get('audio_name', 'Sin nombre')}")
    print(f"   📅 Fecha: {t['created_at']}")
    print(f"   📊 Estado: {t['status']}")
    
    if t.get('summary_content'):
        summary_preview = t['summary_content'][:150] + "..." if len(t['summary_content']) > 150 else t['summary_content']
        print(f"   📝 Resumen: {summary_preview}")
        
        if t.get('summary_prompt'):
            prompt_preview = t['summary_prompt'][:80] + "..." if len(t['summary_prompt']) > 80 else t['summary_prompt']
            print(f"   💬 Prompt usado: {prompt_preview}")
    else:
        print(f"   📝 Resumen: ⏳ Procesando...")
    
    print(f"   " + "-" * 76)

# ============================================================================
# 6. EXAMPLE RESPONSE FORMAT
# ============================================================================
print("\n" + "=" * 80)
print("📄 FORMATO DE RESPUESTA DEL ENDPOINT GET /api/transcriptions/")
print("=" * 80)
print("""
[
  {
    "id": 50,
    "audio_name": "economía.mp3",
    "summary_content": "Resumen final del audio...",
    "summary_prompt": "Prompt usado para generar el resumen",
    "status": "done",
    "created_at": "2025-11-26T11:00:00Z"
  },
  {
    "id": 49,
    "audio_name": "conferencia.mp3",
    "summary_content": null,  // Aún procesando
    "summary_prompt": null,
    "status": "transcribing",
    "created_at": "2025-11-26T10:45:00Z"
  }
]
""")

print("\n✨ API simplificada a 2 endpoints principales:")
print("   1. POST /api/transcriptions/upload/  → Subir audio + prompt")
print("   2. GET  /api/transcriptions/         → Historial con resúmenes")
print("\n🎯 El frontend solo necesita llamar estos 2 endpoints!")
