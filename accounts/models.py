from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_student(self):
        return self.role == 'student'
    
    def save(self, *args, **kwargs):
        # Set is_staff and is_superuser based on role
        if self.role == 'admin':
            self.is_staff = True
            self.is_superuser = True
        elif self.role == 'teacher':
            self.is_staff = True
            self.is_superuser = False
        else:
            self.is_staff = False
            self.is_superuser = False
        super().save(*args, **kwargs)