from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('', views.ChatbotView.as_view(), name='index'),
    path('api/chat/', views.ChatAPIView.as_view(), name='chat_api'),
    path('api/history/<str:session_id>/', views.ChatHistoryView.as_view(), name='chat_history'),
    path('api/test/', views.test_tools, name='test_tools'),
]