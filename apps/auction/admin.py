# apps/auction/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import AuctionServer, AuctionBid, AuctionHistory

@admin.register(AuctionServer)
class AuctionServerAdmin(admin.ModelAdmin):
    list_display = ['name', 'mod', 'slots', 'owner', 'current_price', 'status_badge', 'end_date']
    list_filter = ['status', 'mod', 'created_at', 'end_date']
    search_fields = ['name', 'owner__username', 'mod']
    readonly_fields = ['created_at', 'sold_at', 'gameap_server_id']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'owner')
        }),
        ('Характеристики сервера', {
            'fields': ('mod', 'slots', 'plan', 'ip_address', 'port', 'gameap_server_id')
        }),
        ('Аукцион', {
            'fields': ('starting_price', 'current_price', 'status', 'start_date', 'end_date')
        }),
        ('Продажа', {
            'fields': ('buyer', 'sold_at')
        }),
        ('Система', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'sold': 'blue',
            'cancelled': 'red',
            'expired': 'orange'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'

@admin.register(AuctionBid)
class AuctionBidAdmin(admin.ModelAdmin):
    list_display = ['auction_name', 'bidder', 'bid_amount', 'created_at']
    list_filter = ['auction__mod', 'created_at', 'auction__status']
    search_fields = ['bidder__username', 'auction__name']
    readonly_fields = ['created_at']

    def auction_name(self, obj):
        return obj.auction.name
    auction_name.short_description = 'Аукцион'

@admin.register(AuctionHistory)
class AuctionHistoryAdmin(admin.ModelAdmin):
    list_display = ['auction_name', 'action', 'user', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['auction__name', 'user__username']
    readonly_fields = ['created_at', 'auction', 'action', 'user', 'description']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def auction_name(self, obj):
        return obj.auction.name
    auction_name.short_description = 'Аукцион'