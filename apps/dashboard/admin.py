from django.contrib import admin
from .models import UserStatistic

@admin.register(UserStatistic)
class UserStatisticAdmin(admin.ModelAdmin):
    list_display = ('user', 'servers_count', 'total_balance', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username',)