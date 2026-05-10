from django.urls import path
from . import views

urlpatterns = [
    path('widget/', views.chat_widget, name='chat_widget'),
    path('send/', views.send_message_ajax, name='send_message_ajax'),
    path('messages/', views.get_messages, name='get_messages'),
    path('clear/', views.clear_chat_ajax, name='clear_chat_ajax'),
]