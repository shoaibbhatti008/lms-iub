from django.contrib import admin
from .models import Course, Content

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_code', 'teacher', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'course_code', 'description')
    filter_horizontal = ('students',)

@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'content_type', 'uploaded_by', 'uploaded_at')
    list_filter = ('content_type', 'uploaded_at')
    search_fields = ('title', 'course__title')