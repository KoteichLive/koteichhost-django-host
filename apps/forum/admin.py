# forum/admin.py
from django.contrib import admin
from .models import Category, Topic, Post, PostEdit, ForumRewardConfig

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'created_at']
    list_editable = ['order']
    search_fields = ['name']
    list_filter = ['created_at']

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'is_pinned', 'is_closed', 'views', 'created_at']
    list_filter = ['category', 'is_pinned', 'is_closed', 'created_at']
    search_fields = ['title', 'content']
    list_editable = ['is_pinned', 'is_closed']
    raw_id_fields = ['author', 'category']

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'topic', 'author', 'reward_amount', 'created_at', 'updated_at']
    list_filter = ['created_at', 'topic__category']
    search_fields = ['content']
    raw_id_fields = ['topic', 'author']
    readonly_fields = ['reward_amount']

@admin.register(PostEdit)
class PostEditAdmin(admin.ModelAdmin):
    list_display = ['post', 'editor', 'edited_at', 'reason']
    list_filter = ['edited_at']
    readonly_fields = ['post', 'editor', 'old_content', 'new_content', 'edited_at']
    search_fields = ['reason', 'post__content']

@admin.register(ForumRewardConfig)
class ForumRewardConfigAdmin(admin.ModelAdmin):
    list_display = ['price_per_character', 'min_post_length', 'max_daily_reward', 'enabled']
    fieldsets = (
        ('Основные настройки', {
            'fields': ('price_per_character', 'min_post_length', 'max_daily_reward', 'enabled')
        }),
    )
    
    def has_add_permission(self, request):
        # Разрешаем только одну конфигурацию
        return self.model.objects.count() < 1
    
    def has_delete_permission(self, request, obj=None):
        return False