from django.urls import path
from . import views

urlpatterns = [
    path("balance/", views.balance_view, name="credits-balance"),
    path("history/", views.history_view, name="credits-history"),
    path("verify-purchase/", views.verify_purchase_view, name="credits-verify-purchase"),
]
