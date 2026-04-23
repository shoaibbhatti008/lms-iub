from django.db import models
from django.conf import settings

class Course(models.Model):
    course_id = models.CharField(max_length=20, unique=True)
    course_code = models.CharField(max_length=10)
    title = models.CharField(max_length=200)
    description = models.TextField()
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'teacher'})
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='enrolled_courses', blank=True, limit_choices_to={'role': 'student'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.course_code} - {self.title}"
    
    def get_enrollment_count(self):
        return self.students.count()

class Content(models.Model):
    CONTENT_TYPES = (
        ('file', 'File'),
        ('link', 'Link'),
        ('text', 'Text'),
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    file = models.FileField(upload_to='course_contents/', blank=True, null=True)
    link_url = models.URLField(blank=True, null=True)
    text_content = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Announcement(models.Model):
    PRIORITY_CHOICES = (
        ('normal', '📢 Normal'),
        ('important', '⚠️ Important'),
        ('urgent', '🔥 Urgent'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    attachment = models.FileField(upload_to='announcement_attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']