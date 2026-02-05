# Atenas

Atenas es un sistema completo de transcripción y resumen de audio que utiliza procesamiento asíncrono para convertir archivos de audio en texto transcrito y generar resúmenes inteligentes mediante inteligencia artificial.

## Descripción del Proyecto

Este proyecto proporciona una plataforma que permite a los usuarios subir archivos de audio, transcribirlos automáticamente usando Whisper de OpenAI, y generar resúmenes utilizando la API de Groq. El sistema está dividido en un backend Django REST API y un frontend móvil React Native.

## Arquitectura

El proyecto sigue una arquitectura cliente-servidor con procesamiento asíncrono:

- **Backend**: Django REST Framework con procesamiento asíncrono mediante Celery
- **Frontend**: Aplicación móvil React Native
- **Cola de tareas**: Redis como broker para Celery
- **Modelos de IA**: Whisper para transcripción y Groq para generación de resúmenes

## Características Principales

- Subida de archivos de audio en diversos formatos
- Segmentación automática de audio en chunks para procesamiento paralelo
- Transcripción de audio usando modelos Whisper
- Generación de resúmenes mediante IA con Groq
- Procesamiento asíncrono con seguimiento de estado en tiempo real
- API REST documentada con Swagger/ReDoc
- Autenticación de usuarios y gestión de perfiles
- Aplicación móvil multiplataforma

## Estructura del Proyecto

```
Atenas/
├── backend/
│   ├── django-rest-api/
│   │   ├── config/              # Configuración de Django y Celery
│   │   ├── apps/
│   │   │   ├── api/             # API principal con modelos y tasks
│   │   │   └── users/           # Gestión de usuarios
│   │   └── manage.py
│   ├── environment.yml          # Dependencias de Conda
│   └── .env.example             # Variables de entorno de ejemplo
└── frontend/
    └── atenas_front/            # Aplicación React Native
        └── package.json
```

## Tecnologías Utilizadas

### Backend
- Python 3.x
- Django 4.x
- Django REST Framework
- Celery para tareas asíncranas
- Redis como broker de mensajes
- PostgreSQL como base de datos
- Whisper (OpenAI) para transcripción
- Groq API para generación de resúmenes
- drf-yasg para documentación Swagger

### Frontend
- React Native 0.82.1
- React Navigation para navegación
- Axios para peticiones HTTP
- TypeScript para tipado estático
- AsyncStorage para persistencia local

## Requisitos Previos

- Python 3.8+
- Node.js 20+
- PostgreSQL 12+
- Redis Server
- Conda (recomendado para gestión de entorno)
- Xcode (para iOS) o Android Studio (para Android)

## Instalación

### Backend

1. Clonar el repositorio:
```bash
git clone https://github.com/RenDiego07/Atenas.git
cd Atenas/backend
```

2. Crear y activar el entorno Conda:
```bash
conda env create -f environment.yml
conda activate atenas-backend2
```

3. Navegar al directorio de Django:
```bash
cd django-rest-api
```

4. Instalar dependencias adicionales:
```bash
pip install -r requirements.txt
pip install celery redis openai-whisper groq
```

5. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

6. Configurar la base de datos:
```bash
python manage.py migrate
```

7. Crear un superusuario:
```bash
python manage.py createsuperuser
```

### Frontend

1. Navegar al directorio del frontend:
```bash
cd frontend/atenas_front
```

2. Instalar dependencias:
```bash
npm install
```

3. Para iOS, instalar pods:
```bash
cd ios && pod install && cd ..
```

## Configuración

### Variables de Entorno (Backend)

Configurar el archivo `.env` en `backend/django-rest-api/`:

```env
# Base de datos
DATABASE_NAME=atenas_db
DATABASE_USER=postgres
DATABASE_PASSWORD=tu_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Django
SECRET_KEY=tu-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# APIs de IA
OPENAI_API_KEY=tu-openai-key
GROQ_API_KEY=tu-groq-api-key
```

## Uso

### Iniciar el Backend

1. Iniciar Redis:
```bash
redis-server
```

2. Iniciar el servidor Django (terminal 1):
```bash
cd backend/django-rest-api
conda activate atenas-backend2
python manage.py runserver
```

3. Iniciar Celery Worker (terminal 2):
```bash
cd backend/django-rest-api
conda activate atenas-backend2
celery -A config worker --loglevel=info
```

4. (Opcional) Iniciar Flower para monitoreo de tareas (terminal 3):
```bash
pip install flower
celery -A config flower
# Acceder a http://localhost:5555
```

### Iniciar el Frontend

Para Android:
```bash
npm run android
```

Para iOS:
```bash
npm run ios
```

## API Endpoints

La API REST está documentada con Swagger. Una vez iniciado el servidor, acceder a:

- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

### Endpoints Principales

- `POST /api/transcriptions/upload/` - Subir archivo de audio
- `POST /api/transcriptions/{id}/transcribe/` - Iniciar transcripción
- `GET /api/transcriptions/{id}/chunks/` - Ver progreso de chunks
- `GET /api/users/profile/` - Obtener perfil de usuario
- `PUT /api/users/profile/update/` - Actualizar perfil

## Flujo de Trabajo

1. **Subida**: El usuario sube un archivo de audio
2. **Segmentación**: El sistema divide el audio en chunks
3. **Transcripción**: Celery procesa cada chunk con Whisper
4. **Resumen**: Groq genera resúmenes del texto transcrito
5. **Consulta**: El usuario accede a las transcripciones y resúmenes

### Estados del Sistema

**Transcripción**:
- `uploaded` - Audio subido
- `chunked` - Dividido en segmentos
- `transcribing` - En proceso de transcripción
- `transcribed` - Completado

**Chunks**:
- `ready` - Listo para procesar
- `transcribing` - En proceso
- `done` - Completado

## Modelos de Datos

### Transcription
- Usuario asociado
- Archivo de audio
- Duración total
- Idioma
- Estado del procesamiento
- Prompt personalizado opcional

### TranscriptionChunk
- Referencia a transcripción padre
- Tiempos de inicio/fin
- Texto transcrito
- Estado
- Archivo de chunk
- Resumen generado

### Summary
- Referencia a transcripción
- Encabezado
- URL de enlace
- Prompt utilizado

## Documentación Adicional

- [README del Backend](backend/django-rest-api/README.md)
- [Guía de Configuración de Transcripción](backend/django-rest-api/TRANSCRIPTION_SETUP.md)

## Solución de Problemas

### Celery no puede conectar a Redis
```bash
# Verificar que Redis está corriendo
redis-cli ping
# Debe responder: PONG
```

### Error de memoria con Whisper
- Usar modelos más pequeños: `base` o `tiny`
- Reducir el tamaño de los chunks de audio

### Tareas atascadas en pendiente
- Verificar que el worker de Celery está corriendo
- Revisar los logs del worker para errores
- Verificar la configuración de routing de tareas

