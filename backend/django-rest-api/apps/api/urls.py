from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SummaryViewSet

router = DefaultRouter()
router.register(r'summaries', SummaryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]