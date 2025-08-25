from django.urls import path
from . import views

urlpatterns = [
    path("", views.chat_page, name="chat_page"),
    path("api/", views.chat_api, name="chat_api"),
    path("reset/", views.reset_chat, name="reset_chat"),
]
