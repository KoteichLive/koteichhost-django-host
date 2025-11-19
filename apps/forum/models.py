# forum/models.py (дополнение к существующим)
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def last_topic(self):
        return self.topics.order_by('-created_at').first()

class Topic(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topics')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='topics')
    is_pinned = models.BooleanField(default=False, verbose_name="Закреплено")
    is_closed = models.BooleanField(default=False, verbose_name="Закрыто")
    views = models.IntegerField(default=0, verbose_name="Просмотры")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Тема"
        verbose_name_plural = "Темы"
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return self.title
    
    def last_post(self):
        return self.posts.order_by('-created_at').first()
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('forum:topic_posts', kwargs={'topic_id': self.pk})

class Post(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На одобрении'),
        ('approved', 'Одобрен'),
        ('rejected', 'Отклонен'),
    ]
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(verbose_name="Содержание")
    content_html = models.TextField(verbose_name="HTML контент", blank=True, null=True, editable=False)
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Вознаграждение получено")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    rejection_reason = models.TextField(blank=True, null=True, verbose_name="Причина отклонения")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Сообщение #{self.id} в теме '{self.topic.title}'"
    
    def calculate_reward(self):
        """Рассчитать вознаграждение на основе длины поста"""
        config = ForumRewardConfig.get_config()
        if not config.enabled or len(self.content) < config.min_post_length:
            return 0
        from decimal import Decimal
        reward = Decimal(len(self.content)) * config.price_per_character
        return float(reward)
    
    def is_visible_to(self, user):
        """Проверить, видим ли пост для пользователя"""
        if user == self.author:
            return True
        if user.is_staff:
            return True
        if self.status == 'approved':
            return True
        return False

class PostEdit(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='edits')
    editor = models.ForeignKey(User, on_delete=models.CASCADE)
    old_content = models.TextField(verbose_name="Было")
    new_content = models.TextField(verbose_name="Стало")
    reason = models.CharField(max_length=200, blank=True, verbose_name="Причина")
    edited_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Правка сообщения"
        verbose_name_plural = "Правки сообщений"
        ordering = ['-edited_at']


class ForumRewardConfig(models.Model):
    """Настройка вознаграждений за посты в форуме"""
    price_per_character = models.DecimalField(max_digits=10, decimal_places=4, default=0.01, verbose_name="Цена за символ (₽)")
    min_post_length = models.IntegerField(default=10, verbose_name="Минимальная длина поста (символов)")
    max_daily_reward = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Максимальное дневное вознаграждение (опционально)")
    enabled = models.BooleanField(default=True, verbose_name="Включить вознаграждения")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Настройка вознаграждений форума"
        verbose_name_plural = "Настройки вознаграждений форума"
    
    def __str__(self):
        return f"Вознаграждение: {self.price_per_character}₽ за символ"
    
    @classmethod
    def get_config(cls):
        """Получить или создать конфиг по умолчанию"""
        config, created = cls.objects.get_or_create(pk=1)
        return config