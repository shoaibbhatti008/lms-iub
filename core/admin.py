from django.contrib import admin
from courses.models import Course
from assignments.models import Assignment, Submission

# Re-export for convenience
admin.site.site_header = "LMS Administration"
admin.site.site_title = "LMS Admin Portal"
admin.site.index_title = "Welcome to LMS Admin Panel"