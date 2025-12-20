from rest_framework import viewsets
from .models import Spread
from .serializers import SpreadSerializer

class SpreadViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Spread.objects.all()
    serializer_class = SpreadSerializer
