from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuración de Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="Atenas API",
        default_version='v1',
        description="""
        API para transcripción y resumen de audio usando Whisper y Groq.
        
        ## Características
        - 🎙️ Transcripción automática con Whisper
        - 🤖 Resúmenes inteligentes con Groq (llama-3.3-70b)
        - 📝 Prompts personalizados para resúmenes
        - 📚 Historial completo de transcripciones
        
        ## Autenticación
        Usa JWT Bearer tokens. Obtén un token con POST /api/auth/login/
        """,
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@atenas.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.api.urls')),
    
    # Swagger/OpenAPI Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)