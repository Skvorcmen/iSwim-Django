from django.db import models
from django.conf import settings
from django.utils import timezone

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('new_pr', 'Новый личный рекорд'),
        ('medal', 'Медаль на соревновании'),
        ('competition', 'Соревнование завершено'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
