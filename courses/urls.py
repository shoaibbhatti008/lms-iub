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
    path('students/', views.manage_students, name='manage_students'),
    path('students/delete/<int:student_id>/', views.delete_student, name='delete_student'),
    
    # Announcement URLs
    path('<int:course_id>/announcements/', views.course_announcements, name='course_announcements'),
    path('<int:course_id>/announcements/create/', views.create_announcement, name='create_announcement'),
    path('announcement/delete/<int:announcement_id>/', views.delete_announcement, name='delete_announcement'),
    
    # Lecture URLs
    path('<int:course_id>/lectures/', views.lecture_list, name='lecture_list'),
    path('<int:course_id>/lectures/<int:lecture_id>/', views.lecture_detail, name='lecture_detail'),
    path('<int:course_id>/lectures/create/', views.create_lecture, name='create_lecture'),
    path('lecture/delete/<int:lecture_id>/', views.delete_lecture, name='delete_lecture'),
    path('<int:course_id>/lecture-attendance/', views.lecture_attendance_report, name='lecture_attendance'),
    
    # Live Class URLs
    path('<int:course_id>/live-classes/', views.live_class_list, name='live_class_list'),
    path('<int:course_id>/live-classes/create/', views.create_live_class, name='create_live_class'),
    path('live-class/delete/<int:live_class_id>/', views.delete_live_class, name='delete_live_class'),
    path('live-class/start/<int:live_class_id>/', views.start_live_class, name='start_live_class'),
    path('live-class/<str:meeting_link>/', views.live_class_room, name='live_class_room'),
    path('live-classes/all/', views.live_class_list_all, name='live_class_list_all'),
    path('<int:course_id>/live-attendance/', views.live_class_attendance_list, name='live_class_attendance_list'),
    path('<int:course_id>/live-attendance/<int:live_class_id>/', views.live_class_attendance_detail, name='live_class_attendance_detail'),
    path('<int:course_id>/test-attendance/', views.test_attendance, name='test_attendance'),
    path('<int:course_id>/lecture-attendance/', views.lecture_attendance_report, name='lecture_attendance'),
    path('my-attendance/', views.my_attendance, name='my_attendance'),
]