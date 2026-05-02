from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuestionViewSet, KnowledgePointViewSet, CoursewareView, ChatNoteViewSet

router = DefaultRouter()
router.register(r'questions', QuestionViewSet)
router.register(r'notes', KnowledgePointViewSet, basename='knowledgepoint')
router.register(r'courseware', CoursewareView, basename='courseware')
router.register(r'chat-notes', ChatNoteViewSet, basename='chatnote')

urlpatterns = [
    path('', include(router.urls)),
]
