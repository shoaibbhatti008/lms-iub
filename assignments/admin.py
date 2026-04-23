from django.contrib import admin
from .models import Assignment, Submission

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'deadline', 'max_marks', 'created_at')
    list_filter = ('course', 'deadline', 'created_at')
    search_fields = ('title', 'description', 'course__title')

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'submitted_at', 'marks', 'is_late')
    list_filter = ('assignment__course', 'submitted_at', 'marks')
    search_fields = ('student__username', 'assignment__title')
    
    def is_late(self, obj):
        return obj.is_late()
    is_late.boolean = True