
from django.urls import path
from .views import health_check, chat

urlpatterns = [
    path("health/", health_check, name="health"),
    path("chat/", chat, name="chat"),
]
