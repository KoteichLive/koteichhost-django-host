from django.contrib import admin
from .models import ServerType, ServerPlan, ServerCase, CasePlan, UserServer, ServerTransaction


@admin.register(ServerType)
class ServerTypeAdmin(admin.ModelAdmin):
    """Админка для управления типами серверов"""
    
    list_display = ['icon_title', 'mod_id', 'is_active', 'order', 'updated_at']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['title', 'mod_id']
    list_editable = ['order', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('mod_id', 'title', 'icon', 'description')
        }),
        ('Статус', {
            'fields': ('is_active',),
            'description': 'Отключите, чтобы скрыть сервер из каталога заказов'
        }),
        ('Порядок отображения', {
            'fields': ('order',)
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def icon_title(self, obj):
        return f"{obj.icon} {obj.title}"
    icon_title.short_description = 'Название'


@admin.register(ServerPlan)
class ServerPlanAdmin(admin.ModelAdmin):
    """Админка для управления тарифами серверов"""
    
    list_display = ['server_type', 'name', 'slots', 'price_display', 'is_active']
    list_filter = ['server_type', 'name', 'is_active', 'created_at']
    search_fields = ['server_type__title', 'name']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Выбор типа сервера', {
            'fields': ('server_type',)
        }),
        ('Параметры тарифа', {
            'fields': ('name', 'slots', 'price')
        }),
        ('Дополнительная информация', {
            'fields': ('description',)
        }),
        ('Статус', {
            'fields': ('is_active',),
            'description': 'Отключите, чтобы скрыть тариф из каталога'
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def price_display(self, obj):
        return f"{obj.price}₽/мес"
    price_display.short_description = 'Цена'


class CasePlanInline(admin.TabularInline):
    """Встроенное редактирование тарифов кейса"""
    model = CasePlan
    extra = 1
    fields = ['plan', 'hourly_price', 'is_active']
    list_select_related = ['plan']


@admin.register(ServerCase)
class ServerCaseAdmin(admin.ModelAdmin):
    """Админка для управления кейсами серверов"""
    
    list_display = ['icon_name', 'server_type', 'price_display', 'sold_status', 'is_active', 'order']
    list_filter = ['server_type', 'is_active', 'created_at']
    search_fields = ['name', 'server_type__title']
    list_editable = ['order', 'is_active']
    readonly_fields = ['created_at', 'updated_at', 'sold_count_display']
    inlines = [CasePlanInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('server_type', 'name', 'icon', 'description')
        }),
        ('Стоимость кейса', {
            'fields': ('price',)
        }),
        ('Лимиты продаж', {
            'fields': ('total_limit', 'sold_count_display'),
            'description': 'Установите лимит для ограничения количества продаж'
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
        ('Порядок отображения', {
            'fields': ('order',)
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def icon_name(self, obj):
        return f"{obj.icon} {obj.name}"
    icon_name.short_description = 'Название'
    
    def price_display(self, obj):
        return f"{obj.price}₽"
    price_display.short_description = 'Цена'
    
    def sold_status(self, obj):
        """Отображение статуса продаж"""
        if obj.total_limit is None:
            return f"📈 Продано: {obj.sold_count}"
        else:
            remaining = obj.available_count
            if remaining <= 0:
                return f"🔴 Продано: {obj.sold_count}/{obj.total_limit} (РАСПРОДАНО)"
            elif remaining <= 5:
                return f"🟡 Продано: {obj.sold_count}/{obj.total_limit} ({remaining} осталось)"
            else:
                return f"🟢 Продано: {obj.sold_count}/{obj.total_limit}"
    sold_status.short_description = 'Статус продаж'
    
    def sold_count_display(self, obj):
        """Количество проданных кейсов"""
        if obj.total_limit is None:
            return f"{obj.sold_count} (неограниченно)"
        else:
            return f"{obj.sold_count} из {obj.total_limit} ({obj.available_count} осталось)"
    sold_count_display.short_description = 'Продано'


@admin.register(CasePlan)
class CasePlanAdmin(admin.ModelAdmin):
    """Админка для управления тарифами в кейсах"""
    
    list_display = ['case', 'plan', 'hourly_price_display', 'is_active']
    list_filter = ['case__server_type', 'is_active', 'case']
    search_fields = ['case__name', 'plan__server_type__title']
    list_editable = ['is_active']
    readonly_fields = ['created_at'] if hasattr(CasePlan, 'created_at') else []
    
    fieldsets = (
        ('Выбор', {
            'fields': ('case', 'plan')
        }),
        ('Цена в час', {
            'fields': ('hourly_price',)
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
    )
    
    def hourly_price_display(self, obj):
        return f"{obj.hourly_price}₽/ч"
    hourly_price_display.short_description = 'Цена в час'


@admin.register(UserServer)
class UserServerAdmin(admin.ModelAdmin):
    """Админка для управления серверами пользователей"""
    
    list_display = ['name', 'user', 'case', 'status', 'balance_display', 'created_at']
    list_filter = ['status', 'created_at', 'case__server_type']
    search_fields = ['name', 'user__username', 'gameap_id']
    readonly_fields = ['gameap_id', 'created_at', 'updated_at', 'last_charged', 'deleted_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'name', 'case', 'plan')
        }),
        ('Идентификаторы', {
            'fields': ('gameap_id',)
        }),
        ('Баланс', {
            'fields': ('balance',),
            'description': 'Отдельный баланс сервера для оплаты часов работы'
        }),
        ('Статус', {
            'fields': ('status',)
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at', 'last_charged', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )
    
    def balance_display(self, obj):
        return f"{obj.balance}₽"
    balance_display.short_description = 'Баланс'


@admin.register(ServerTransaction)
class ServerTransactionAdmin(admin.ModelAdmin):
    """Админка для просмотра транзакций серверов"""
    
    list_display = ['server', 'transaction_type', 'amount_display', 'balance_after_display', 'created_at']
    list_filter = ['transaction_type', 'created_at', 'server__case__server_type']
    search_fields = ['server__name', 'server__user__username', 'description']
    readonly_fields = [
        'server', 'amount', 'transaction_type', 'description',
        'balance_before', 'balance_after', 'created_at'
    ]
    
    fieldsets = (
        ('Информация о транзакции', {
            'fields': ('server', 'transaction_type', 'description')
        }),
        ('Сумма и баланс', {
            'fields': ('amount', 'balance_before', 'balance_after')
        }),
        ('Время', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        """Транзакции создаются автоматически, не вручную"""
        return False
    
    def amount_display(self, obj):
        return f"{obj.amount}₽"
    amount_display.short_description = 'Сумма'
    
    def balance_after_display(self, obj):
        return f"{obj.balance_after}₽"
    balance_after_display.short_description = 'Баланс после'
