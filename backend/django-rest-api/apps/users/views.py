from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserSerializer, UserProfileUpdateSerializer

@swagger_auto_schema(
    method='get',
    operation_summary="Obtener perfil del usuario",
    operation_description="Devuelve la información del usuario autenticado actualmente",
    tags=['Usuarios'],
    responses={
        200: openapi.Response(
            description="Información del usuario",
            schema=UserSerializer,
            examples={
                "application/json": {
                    "id": 1,
                    "username": "Fer",
                    "email": "fer@example.com",
                    "first_name": "Fernando",
                    "last_name": "López"
                }
            }
        ),
        401: "No autenticado"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    return Response(UserSerializer(request.user).data)

@swagger_auto_schema(
    methods=['put', 'patch'],
    operation_summary="Actualizar perfil del usuario",
    operation_description="""
    Actualiza la información del perfil del usuario autenticado.
    
    - PUT: Actualización completa (requiere todos los campos)
    - PATCH: Actualización parcial (solo los campos enviados)
    """,
    tags=['Usuarios'],
    request_body=UserProfileUpdateSerializer,
    responses={
        200: openapi.Response(
            description="Perfil actualizado exitosamente",
            schema=UserSerializer,
            examples={
                "application/json": {
                    "id": 1,
                    "username": "Fer",
                    "email": "nuevo_email@example.com",
                    "first_name": "Fernando",
                    "last_name": "López"
                }
            }
        ),
        400: "Datos inválidos",
        401: "No autenticado"
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    serializer = UserProfileUpdateSerializer(
        request.user, 
        data=request.data, 
        partial=request.method == 'PATCH'
    )
    if serializer.is_valid():
        serializer.save()
        return Response(UserSerializer(request.user).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)