from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

class ChatMessage(models.Model):
    MESSAGE_TYPES = [
        ('ai', 'AI Чат'),
        ('user', 'Личное сообщение'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='received_messages')
    message = models.TextField()
    response = models.TextField(blank=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='ai')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Сообщение чата'
        verbose_name_plural = 'Сообщения чата'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.message_type == 'ai':
            return f"AI Chat: {self.user.username}"
        else:
            return f"{self.user.username} -> {self.recipient.username}"

class KnowledgeBase(models.Model):
    CATEGORY_CHOICES = [
        ('about', 'О компании'),
        ('services', 'Услуги'),
        ('products', 'Продукты'),
        ('contacts', 'Контакты'),
        ('general', 'Общая информация'),
    ]
    
    question = models.CharField(max_length=255, verbose_name='Вопрос/Ключевое слово')
    answer = models.TextField(verbose_name='Ответ')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general', verbose_name='Категория')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    priority = models.IntegerField(default=1, verbose_name='Приоритет (1-10)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'База знаний'
        verbose_name_plural = 'База знаний'
        ordering = ['priority', '-created_at']
    
    def __str__(self):
        return f"{self.question} ({self.category})"


class ChatAdminMessage(models.Model):
    """Сообщения от администрации пользователю (отдельная сущность)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_messages')
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_admin_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Сообщение администрации'
        verbose_name_plural = 'Сообщения администрации'
        ordering = ['-created_at']

    def __str__(self):
        return f"Admin -> {self.user.username}: {self.content[:30]}"


class ChatRestriction(models.Model):
    """Ограничение прав пользователя в чатах/форуме/просмотре сервера.

    Админ может выставить ограничение с ценой выкупа. Пока ограничение активно,
    пользователь не может отправлять сообщения (только читать)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chat_restriction')
    restricted_write = models.BooleanField(default=False, help_text='Если True — пользователь не может писать')
    restrict_forum_reply = models.BooleanField(default=False, help_text='Отключить возможность оставлять ответы в форуме')
    restrict_server_view = models.BooleanField(default=False, help_text='Отключить просмотр вкладки сервера')
    purchasable = models.BooleanField(default=False, help_text='Можно ли выкупить право писать')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_restrictions')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Ограничение чата'
        verbose_name_plural = 'Ограничения чата'

    def is_active(self):
        if not self.active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def __str__(self):
        return f"Restriction: {self.user.username} (write={'no' if self.restricted_write else 'yes'})"


class SupportTicket(models.Model):
    """Система тикетов техподдержки для входящих сообщений пользователей"""
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('in_progress', 'В процессе'),
        ('waiting', 'Ожидание ответа'),
        ('resolved', 'Решен'),
        ('closed', 'Закрыт'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=255, verbose_name='Тема')
    message = models.TextField(verbose_name='Сообщение')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name='Приоритет')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='Статус')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано администратором')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Последнее обновление')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', verbose_name='Назначено')
    
    class Meta:
        verbose_name = 'Тикет техподдержки'
        verbose_name_plural = 'Тикеты техподдержки'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_read']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"[{self.get_status_display()}] {self.subject} от {self.user.username}"
    
    @classmethod
    def get_unread_count(cls):
        """Получить количество непрочитанных тикетов"""
        return cls.objects.filter(is_read=False).count()


class TicketReply(models.Model):
    """Ответы в тикетах техподдержки"""
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_replies')
    content = models.TextField(verbose_name='Ответ')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    
    class Meta:
        verbose_name = 'Ответ в тикете'
        verbose_name_plural = 'Ответы в тикетах'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Reply to {self.ticket.id} by {self.author.username}"