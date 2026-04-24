from django.db import models
from django.conf import settings
from exams.models import Exam

class UserExamSession(models.Model):
    # Changed to ForeignKey. You must enforce the "only one active session" rule in your view logic.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_sessions')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    
    STAGE_CHOICES = [
        ('login', 'Login'),
        ('instructions', 'Instructions'),
        ('exam_started', 'Exam Started'),
        ('exam_ended', 'Exam Ended')
    ]
    current_stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='login')
    
    MODE_CHOICES = [
        ('test', 'Test'),
        ('simulation', 'Simulation')
    ]
    exam_mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    
    session_start_time = models.DateTimeField(null=True, blank=True)
    exam_start_time = models.DateTimeField(null=True, blank=True)
    
    interface_behavior = models.JSONField(default=dict) 
    
    session_recording = models.JSONField(default=dict)

    last_heartbeat = models.DateTimeField(null=True, blank=True)
    compensatory_time_secs = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} ({self.current_stage})"