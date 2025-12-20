from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SpreadViewSet

router = DefaultRouter()
router.register(r'spreads', SpreadViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
