# apps/auction/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

class Auction(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='active')
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='auctions')

    def __str__(self):
        return self.title

class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='bids')
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Bid by {self.bidder} on {self.auction}'

# ДОБАВЬТЕ ЭТИ МОДЕЛИ ДЛЯ АДМИНКИ
class AuctionServer(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активный'),
        ('sold', 'Продан'),
        ('cancelled', 'Отменен'),
        ('expired', 'Истек')
    ]
    
    name = models.CharField(max_length=100, verbose_name='Название сервера')
    description = models.TextField(blank=True, verbose_name='Описание')
    mod = models.CharField(max_length=50, verbose_name='Модификация')
    slots = models.PositiveIntegerField(verbose_name='Количество слотов')
    plan = models.CharField(max_length=50, default='Basic', verbose_name='Тариф')
    ip_address = models.GenericIPAddressField(verbose_name='IP адрес')
    port = models.PositiveIntegerField(verbose_name='Порт')
    gameap_server_id = models.CharField(max_length=50, blank=True, verbose_name='ID в GameAP')
    
    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='auction_servers', verbose_name='Владелец')
    buyer = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='purchased_servers', verbose_name='Покупатель')
    
    starting_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Начальная цена')
    current_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='Текущая цена')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Статус')
    
    start_date = models.DateTimeField(auto_now_add=True, verbose_name='Начало аукциона')
    end_date = models.DateTimeField(verbose_name='Окончание аукциона')
    sold_at = models.DateTimeField(null=True, blank=True, verbose_name='Время продажи')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')

    def __str__(self):
        return self.name

class AuctionBid(models.Model):
    """Ставки на аукционе"""
    auction = models.ForeignKey(AuctionServer, on_delete=models.CASCADE, related_name='bids', verbose_name='Аукцион')
    bidder = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name='Ставка от')
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма ставки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время ставки')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ставка на аукционе'
        verbose_name_plural = 'Ставки на аукционах'

    def __str__(self):
        return f'{self.bidder.username} - {self.bid_amount}₽'

class AuctionHistory(models.Model):
    """История действий на аукционе"""
    ACTION_CHOICES = [
        ('created', 'Создан'),
        ('bid', 'Ставка'),
        ('sold', 'Продан'),
        ('cancelled', 'Отменен'),
        ('expired', 'Истек')
    ]
    
    auction = models.ForeignKey(AuctionServer, on_delete=models.CASCADE, related_name='history', verbose_name='Аукцион')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='Действие')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name='Пользователь')
    description = models.TextField(blank=True, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время действия')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'История аукциона'
        verbose_name_plural = 'История аукционов'

    def __str__(self):
        return f'{self.auction.name} - {self.get_action_display()}'