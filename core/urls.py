from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('announcements/', views.announcements, name='announcements'),
    path('lectures/', views.all_lectures, name='lecture_list_all'),
    path('live-classes/', views.live_class_list_all, name='live_class_list_all'),
    path('my-attendance/', views.my_attendance, name='my_attendance'),
]