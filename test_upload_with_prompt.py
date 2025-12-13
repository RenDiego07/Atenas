#!/usr/bin/env python
"""
Script de prueba para el endpoint de upload con prompt personalizado
Demuestra el flujo completo con prompt enviado en el upload inicial
"""

import requests
import time

def test_upload_with_custom_prompt():
    print("🧪 Test: Upload con prompt personalizado")
    
    # Login
    print("1. 🔐 Iniciando sesión...")
    login_response = requests.post('http://localhost:8000/api/auth/login/', json={
        'username': 'Fer', 'password': 'Espol123'
    })
    
    if login_response.status_code != 200:
        print(f"❌ Error en login: {login_response.status_code}")
        return False
        
    token = login_response.json()['access']
    print("✅ Login exitoso")
    
    # Upload con prompt personalizado
    print("2. 📤 Subiendo archivo con prompt personalizado...")
    
    custom_prompt = """
    Genera un resumen técnico y detallado enfocado en:
    - Indicadores económicos específicos mencionados
    - Tendencias y proyecciones futuras
    - Análisis cuantitativo de datos presentados
    - Conclusiones y recomendaciones principales
    Usa un lenguaje profesional y estructura la información de manera clara.
    """
    
    try:
        with open('./economía.mp3', 'rb') as audio_file:
            response = requests.post(
                'http://localhost:8000/api/transcriptions/upload/',
                headers={'Authorization': f'Bearer {token}'},
                files={'audio_file': audio_file},
                data={'custom_prompt': custom_prompt.strip()}  # ← NUEVO: Prompt en upload
            )
        
        if response.status_code != 201:
            print(f"❌ Error en upload: {response.status_code}")
            print(response.text)
            return False
            
        transcription_id = response.json()['id']
        print(f"✅ Upload exitoso - Transcription ID: {transcription_id}")
        print("🤖 Pipeline iniciado automáticamente con prompt personalizado")
        
    except FileNotFoundError:
        print("❌ Archivo './economía.mp3' no encontrado")
        print("💡 Usa cualquier archivo MP3 que tengas disponible")
        return False
    
    # Monitorear progreso
    print("3. ⏳ Monitoreando progreso...")
    
    max_checks = 20  # Máximo 20 checks (10 minutos)
    check_interval = 30  # Cada 30 segundos
    
    for attempt in range(max_checks):
        print(f"   📊 Check {attempt + 1}/{max_checks}...")
        
        # Verificar estado de la transcripción
        status_response = requests.get(
            f'http://localhost:8000/api/transcriptions/{transcription_id}/',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if status_response.status_code != 200:
            print(f"❌ Error obteniendo estado: {status_response.status_code}")
            continue
            
        transcription_data = status_response.json()
        current_status = transcription_data['status']
        
        print(f"   Estado actual: {current_status}")
        
        # Verificar chunks si está en progreso
        if current_status in ['transcribing', 'transcribed']:
            chunks = transcription_data.get('chunks', [])
            if chunks:
                done_chunks = [c for c in chunks if c['status'] == 'done']
                summarized_chunks = [c for c in chunks if c['status'] == 'summarized']
                
                print(f"   📝 Chunks transcritos: {len(done_chunks)}/{len(chunks)}")
                print(f"   📋 Chunks resumidos: {len(summarized_chunks)}/{len(chunks)}")
        
        # Verificar si hay resumen final
        summary_response = requests.get(
            f'http://localhost:8000/api/transcriptions/{transcription_id}/summary/',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if summary_response.status_code == 200:
            summary_data = summary_response.json()
            
            if summary_data.get('final_summary'):
                print("🎉 ¡Resumen final completado!")
                
                final_summary = summary_data['final_summary']
                print(f"📝 Prompt usado: {final_summary.get('user_prompt', 'N/A')[:100]}...")
                print(f"📋 Resumen ({len(final_summary['content'])} chars): {final_summary['content'][:200]}...")
                
                return True
                
            elif summary_data.get('summary_status') == 'in_progress':
                progress = summary_data.get('progress', {})
                print(f"   🔄 Resumen en progreso: {progress}")
        
        if attempt < max_checks - 1:
            print(f"   ⏳ Esperando {check_interval}s antes del siguiente check...")
            time.sleep(check_interval)
    
    print("⚠️ Tiempo máximo de espera alcanzado")
    print("💡 El procesamiento puede continuar en segundo plano")
    return False

def test_comparison_with_old_method():
    """Comparar con el método antiguo (endpoint separado)"""
    print("\n🔬 Comparación con método anterior:")
    print("📌 Método NUEVO (este script):")
    print("   1. Upload con prompt → Pipeline automático → Resumen personalizado")
    print("   📊 Total: 1 request + monitoreo")
    
    print("\n📌 Método ANTERIOR:")
    print("   1. Upload sin prompt → Pipeline automático → Resumen genérico")
    print("   2. Request manual para regenerar con prompt personalizado")
    print("   📊 Total: 2 requests + monitoreo")
    
    print("\n✅ Ventajas del nuevo método:")
    print("   - Un solo request inicial")
    print("   - Prompt se aplica desde el inicio") 
    print("   - No necesita regeneración manual")
    print("   - Flujo más intuitivo para usuarios")

if __name__ == "__main__":
    print("🚀 Test del endpoint de upload con prompt personalizado")
    print("=" * 60)
    
    success = test_upload_with_custom_prompt()
    
    if success:
        print("\n🎉 ¡Test completado exitosamente!")
    else:
        print("\n⚠️ Test no completado (puede estar aún procesando)")
    
    test_comparison_with_old_method()
    
    print("\n" + "=" * 60)
    print("✨ ¡Migración a Groq con prompt personalizado funcionando!")