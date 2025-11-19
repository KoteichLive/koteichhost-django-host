from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserStatistic(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    servers_count = models.IntegerField(default=0)
    total_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Статистика пользователя'
        verbose_name_plural = 'Статистика пользователей'