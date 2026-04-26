from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuestionViewSet, KnowledgePointViewSet

router = DefaultRouter()
router.register(r'questions', QuestionViewSet)
router.register(r'notes', KnowledgePointViewSet, basename='knowledgepoint')

urlpatterns = [
    path('', include(router.urls)),
]
