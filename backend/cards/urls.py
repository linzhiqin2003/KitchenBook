from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import viewsets
from .models import TarotCard
from .serializers import TarotCardSerializer

class TarotCardViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for listing and retrieving tarot cards."""
    queryset = TarotCard.objects.all()
    serializer_class = TarotCardSerializer

router = DefaultRouter()
router.register(r'cards', TarotCardViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
