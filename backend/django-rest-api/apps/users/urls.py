from django.urls import path
from .views import profile, update_profile

urlpatterns = [
    path('profile/', profile, name='user-profile'),
    path('profile/update/', update_profile, name='user-profile-update'),
]