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
    CONTENT_TYPES = (('file', 'File'), ('link', 'Link'), ('text', 'Text'))
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
    PRIORITY_CHOICES = (('normal', '📢 Normal'), ('important', '⚠️ Important'), ('urgent', '🔥 Urgent'))
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    attachment = models.FileField(upload_to='announcement_attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Lecture(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lectures')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_url = models.URLField(help_text="YouTube or Vimeo video URL")
    duration = models.CharField(max_length=20, blank=True, help_text="e.g., 45:30")
    order = models.IntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def get_embed_url(self):
        if 'youtube.com' in self.video_url or 'youtu.be' in self.video_url:
            if 'youtu.be' in self.video_url:
                video_id = self.video_url.split('/')[-1].split('?')[0]
            elif 'watch?v=' in self.video_url:
                video_id = self.video_url.split('v=')[1].split('&')[0]
            else:
                return self.video_url
            return f"https://www.youtube.com/embed/{video_id}"
        return self.video_url

class LectureAttendance(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lecture_attendances', limit_choices_to={'role': 'student'})
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='attendances')
    watched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'lecture']
    
    def __str__(self):
        return f"{self.student.username} - {self.lecture.title}"

class LiveClass(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='live_classes')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    meeting_link = models.CharField(max_length=100, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.meeting_link:
            import uuid
            self.meeting_link = str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)
    
    def update_status(self):
        from django.utils import timezone
        now = timezone.now()
        if now > self.end_time:
            self.status = 'completed'
        elif self.start_time <= now <= self.end_time:
            self.status = 'ongoing'
        else:
            self.status = 'scheduled'
        self.save()

class LiveClassAttendance(models.Model):
    live_class = models.ForeignKey(LiveClass, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    joined_at = models.DateTimeField(auto_now_add=True)
    is_present = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['live_class', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.live_class.title}"