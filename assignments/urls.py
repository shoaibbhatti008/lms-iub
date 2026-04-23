from django.urls import path
from . import views

urlpatterns = [
    path('', views.assignment_list, name='assignment_list'),
    path('<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('create/<int:course_id>/', views.create_assignment, name='create_assignment'),
    path('<int:assignment_id>/delete/', views.delete_assignment, name='delete_assignment'),
    path('submit/<int:assignment_id>/', views.submit_assignment, name='submit_assignment'),
    path('grade/<int:submission_id>/', views.grade_submission, name='grade_submission'),
]