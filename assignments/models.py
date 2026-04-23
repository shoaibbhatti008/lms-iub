from django.db import models
from django.conf import settings
from courses.models import Course

class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    deadline = models.DateTimeField()
    max_marks = models.IntegerField(default=100)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # ADD THIS FIELD - attachment
    attachment = models.FileField(upload_to='assignment_attachments/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def is_deadline_passed(self):
        from django.utils import timezone
        return timezone.now() > self.deadline

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    
    # Student answer fields
    answer_text = models.TextField(blank=True, null=True)
    answer_file = models.FileField(upload_to='student_answers/', blank=True, null=True)
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    marks = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='graded_submissions')
    graded_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.assignment.title} - {self.student.username}"
    
    def is_late(self):
        return self.submitted_at > self.assignment.deadline