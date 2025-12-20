from django.urls import path
from .views import DivinationView

urlpatterns = [
    path('divine/', DivinationView.as_view(), name='divine'),
]
