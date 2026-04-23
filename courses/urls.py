from django.urls import path
from . import views

urlpatterns = [
    # Course URLs
    path('', views.course_list, name='course_list'),
    path('create/', views.create_course, name='create_course'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/delete/', views.delete_course, name='delete_course'),
    
    # Content URLs
    path('<int:course_id>/upload/', views.upload_content, name='upload_content'),
    path('content/delete/<int:content_id>/', views.delete_content, name='delete_content'),
    
    # Enrollment URLs
    path('<int:course_id>/enroll/', views.enroll_student, name='enroll_student'),
    path('<int:course_id>/remove/<int:student_id>/', views.remove_student, name='remove_student'),
    
    # Student Management URLs (NEW)
    path('students/', views.manage_students, name='manage_students'),
    path('students/delete/<int:student_id>/', views.delete_student, name='delete_student'),
    
    # Announcement URLs
    path('<int:course_id>/announcements/', views.course_announcements, name='course_announcements'),
    path('<int:course_id>/announcements/create/', views.create_announcement, name='create_announcement'),
    path('announcement/delete/<int:announcement_id>/', views.delete_announcement, name='delete_announcement'),
]