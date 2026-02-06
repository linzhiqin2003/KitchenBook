from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import ExchangeRateView, ReceiptViewSet, StatsOverviewView

router = DefaultRouter()
router.register(r"receipts", ReceiptViewSet, basename="receipt")

urlpatterns = [
    path("", include(router.urls)),
    path("stats/overview/", StatsOverviewView.as_view(), name="stats-overview"),
    path("exchange-rate/", ExchangeRateView.as_view(), name="exchange-rate"),
]
