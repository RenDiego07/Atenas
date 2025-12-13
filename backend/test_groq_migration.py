#!/usr/bin/env python
"""
Script de prueba para verificar la migración de Ollama a Groq
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/Users/dfflores/Developer/Atenas/backend/django-rest-api')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_groq_import():
    """Prueba que se pueda importar Groq"""
    try:
        from groq import Groq
        print("✅ Groq importado correctamente")
        return True
    except ImportError as e:
        print(f"❌ Error importando Groq: {e}")
        return False

def test_groq_api_key():
    """Prueba que la API key esté configurada"""
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            print(f"✅ GROQ_API_KEY configurada (terminación: ...{api_key[-4:]})")
            return True
        else:
            print("❌ GROQ_API_KEY no encontrada en variables de entorno")
            print("💡 Agrega GROQ_API_KEY=tu-api-key al archivo .env")
            return False
    except Exception as e:
        print(f"❌ Error verificando API key: {e}")
        return False

def test_groq_connection():
    """Prueba conexión básica a Groq API"""
    try:
        if not os.environ.get("GROQ_API_KEY"):
            print("⚠️  Saltando test de conexión - no hay API key")
            return False
            
        from groq import Groq
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        # Test básico
        response = client.chat.completions.create(
            messages=[{
                "role": "user", 
                "content": "Responde solo 'OK' si puedes procesar este mensaje"
            }],
            model="llama-3.3-70b-versatile",
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        if "OK" in result.upper():
            print("✅ Conexión a Groq API exitosa")
            print(f"   Respuesta: {result}")
            return True
        else:
            print(f"⚠️  Respuesta inesperada: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error conectando a Groq API: {e}")
        return False

def test_tasks_import():
    """Prueba que se puedan importar las tareas modificadas"""
    try:
        from apps.api.tasks import _call_groq_api, generate_chunk_summary
        print("✅ Funciones de tasks importadas correctamente")
        return True
    except ImportError as e:
        print(f"❌ Error importando tasks: {e}")
        return False

def main():
    print("🔄 Verificando migración de Ollama a Groq...")
    print("=" * 50)
    
    tests = [
        ("Importación de Groq", test_groq_import),
        ("Configuración de API Key", test_groq_api_key),
        ("Importación de Tasks", test_tasks_import),
        ("Conexión a Groq API", test_groq_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        result = test_func()
        results.append(result)
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN:")
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print(f"✅ Todos los tests pasaron ({success_count}/{total_count})")
        print("🚀 La migración está lista para usar")
    else:
        print(f"⚠️  {success_count}/{total_count} tests pasaron")
        print("🔧 Revisa los errores arriba antes de continuar")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)