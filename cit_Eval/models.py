from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    department = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"
    
class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    faculty = models.ForeignKey(User, on_delete=models.CASCADE, related_name='taught_courses')
    students = models.ManyToManyField(User, related_name='enrolled_courses')

    def __str__(self):
        return self.name

class EvaluationSession(models.Model):
    """Defines the timeframe for an evaluation (e.g., 'Fall 2026')"""
    title = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

class Evaluation(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    faculty = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evaluations_received')
    # We don't link 'student' here to keep it anonymous in the database
    
    # Metrics (1-5 Scale)
    teaching_quality = models.IntegerField()
    punctuality = models.IntegerField()
    course_content = models.IntegerField()
    
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class DHSession(models.Model):
    """
    Stores temporary public keys for the DH Handshake.
    In production, you'd likely use Redis for this, but Postgres works for dev.
    """
    session_id = models.CharField(max_length=255, unique=True)
    client_public_key = models.TextField() # Key 'A' from React
    server_private_key = models.TextField() # Key 'b' kept on Django
    shared_secret = models.TextField(null=True, blank=True) # The final 's'
    created_at = models.DateTimeField(auto_now_add=True)