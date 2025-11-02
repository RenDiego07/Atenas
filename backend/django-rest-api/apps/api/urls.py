from django.urls import path, include

urlpatterns = [
    path('auth/', include('apps.authentication.urls')),
    path('users/', include('apps.users.urls')),
    path('transcriptions/', include('apps.transcriptions.urls'))
]