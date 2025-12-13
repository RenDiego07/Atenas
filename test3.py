import requests
import time

def main():
    # Login
    print("🔐 Iniciando sesión...")
    login_response = requests.post('http://localhost:8000/api/auth/login/', json={
        'username': 'Fer', 'password': 'Espol123'
    })
    
    if login_response.status_code != 200:
        print(f"❌ Error en login: {login_response.json()}")
        return
    
    token = login_response.json()['access']
    print("✅ Login exitoso\n")

    # Upload con espera síncrona
    print("📤 Subiendo audio (esperando hasta que termine)...")
    print("⏳ Esto puede tardar varios minutos...\n")
    
    start = time.time()
    
    with open('./economía.mp3', 'rb') as audio_file:
        response = requests.post(
            'http://localhost:8000/api/transcriptions/upload/',
            headers={'Authorization': f'Bearer {token}'},
            files={'audio_file': audio_file},
            data={
                'custom_prompt': 'Resume destacando puntos clave y conceptos importantes'
            },
            timeout=660  # 11 minutos (más que el timeout del servidor)
        )

    elapsed = time.time() - start
    
    print(f"\n📊 Status Code: {response.status_code}")
    print(f"⏱️  Tiempo total: {elapsed:.2f} segundos\n")
    
    if response.status_code == 201:
        data = response.json()
        print("✅ RESUMEN COMPLETO:")
        print("=" * 80)
        print(f"🎵 Audio: {data['audio_name']}")
        print(f"📋 ID: {data['id']}")
        print(f"⏱️  Procesamiento: {data.get('processing_time', 'N/A')}s")
        print(f"\n📝 RESUMEN:")
        print(data['summary_content'])
        print("=" * 80)
        
    elif response.status_code == 202:
        data = response.json()
        print("⏰ TIMEOUT ALCANZADO (aún procesando):")
        print(f"   ID: {data['id']}")
        print(f"   Estado: {data['status']}")
        print(f"   Mensaje: {data['message']}")
        print(f"\n💡 Consulta el historial para ver el resultado:")
        print(f"   GET /api/transcriptions/")
        
    else:
        print(f"❌ Error:")
        print(response.json())

if __name__ == "__main__":
    main()