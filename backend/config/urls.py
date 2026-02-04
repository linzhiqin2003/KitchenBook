from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("api/questiongen/", include("questions.urls")),  # QuestionGen 刷题模块
    path("api/interpretation/", include("apps.interpretation.urls")),
    path("api/emoji/", include("apps.emoji_generator.urls")),
    path("receipts/api/auth/", include("accounts.urls")),
    path("receipts/api/", include("receipts.urls")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
