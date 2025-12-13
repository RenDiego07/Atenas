from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserRegistrationSerializer, UserLoginSerializer  
from apps.users.serializers import UserSerializer

@swagger_auto_schema(
    method='post',
    operation_summary="Registrar nuevo usuario",
    operation_description="Crea una nueva cuenta de usuario y devuelve tokens JWT para autenticación",
    tags=['Autenticación'],
    request_body=UserRegistrationSerializer,
    responses={
        201: openapi.Response(
            description="Usuario registrado exitosamente",
            examples={
                "application/json": {
                    "user": {
                        "id": 1,
                        "username": "usuario123",
                        "email": "usuario@example.com"
                    },
                    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
                }
            }
        ),
        400: "Datos inválidos o usuario ya existe"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)  
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    operation_summary="Iniciar sesión",
    operation_description="""
    Autentica al usuario y devuelve tokens JWT.
    
    Usa el access token en el header: Authorization: Bearer {access_token}
    El refresh token puede usarse para obtener nuevos access tokens cuando expiren.
    """,
    tags=['Autenticación'],
    request_body=UserLoginSerializer,
    responses={
        200: openapi.Response(
            description="Login exitoso",
            examples={
                "application/json": {
                    "user": {
                        "id": 1,
                        "username": "Fer",
                        "email": "fer@example.com"
                    },
                    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
                }
            }
        ),
        400: "Credenciales inválidas"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)