from django.contrib import admin
from .models import ChatRestriction, ChatAdminMessage, SupportTicket, TicketReply, KnowledgeBase

class ChatRestrictionAdmin(admin.ModelAdmin):
    list_display = ('user', 'restricted_write', 'purchasable', 'price', 'active', 'expires_at')
    list_filter = ('restricted_write', 'purchasable', 'active', 'expires_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)

class ChatAdminMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'admin', 'content_preview', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'admin__username', 'content')
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Сообщение'

class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'subject_preview', 'status', 'priority', 'is_read', 'created_at')
    list_filter = ('status', 'priority', 'is_read', 'created_at')
    search_fields = ('user__username', 'subject', 'message')
    readonly_fields = ('created_at', 'updated_at')
    
    def subject_preview(self, obj):
        return obj.subject[:50] + '...' if len(obj.subject) > 50 else obj.subject
    subject_preview.short_description = 'Тема'

class TicketReplyAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'author', 'content_preview', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('ticket__subject', 'author__username', 'content')
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Ответ'

class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'is_active', 'priority', 'created_at', 'updated_at')
    list_filter = ('category', 'is_active', 'created_at', 'updated_at')
    search_fields = ('question', 'answer')
    readonly_fields = ('created_at', 'updated_at')
    
    def question_preview(self, obj):
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Вопрос'

admin.site.register(ChatRestriction, ChatRestrictionAdmin)
admin.site.register(ChatAdminMessage, ChatAdminMessageAdmin)
admin.site.register(SupportTicket, SupportTicketAdmin)
admin.site.register(TicketReply, TicketReplyAdmin)
admin.site.register(KnowledgeBase, KnowledgeBaseAdmin)