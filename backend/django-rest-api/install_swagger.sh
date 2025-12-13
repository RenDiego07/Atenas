#!/bin/bash

# Script de instalación de Swagger para Atenas Backend
# Ejecutar con: bash install_swagger.sh

echo "🚀 Instalando drf-yasg para documentación Swagger..."
echo ""

# Verificar si estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Este script debe ejecutarse desde el directorio django-rest-api/"
    echo "   cd backend/django-rest-api"
    exit 1
fi

# Instalar drf-yasg
echo "📦 Instalando drf-yasg..."
pip install drf-yasg

# Verificar instalación
if python -c "import drf_yasg" 2>/dev/null; then
    echo "✅ drf-yasg instalado correctamente"
else
    echo "❌ Error: drf-yasg no se pudo instalar"
    exit 1
fi

echo ""
echo "✨ Instalación completada!"
echo ""
echo "📚 Para acceder a la documentación:"
echo "   1. Inicia el servidor: python manage.py runserver"
echo "   2. Abre tu navegador en:"
echo "      - Swagger UI: http://localhost:8000/swagger/"
echo "      - ReDoc:      http://localhost:8000/redoc/"
echo ""
echo "📖 Lee SWAGGER_SETUP.md para más información"
