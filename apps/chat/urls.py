from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('send/', views.send_message, name='send_message'),
    path('history/', views.get_chat_history, name='get_history'),
    path('check-new/', views.check_new_messages, name='check_new_messages'),
    path('users/', views.get_users_list, name='get_users'),
    path('mark-read/', views.mark_as_read, name='mark_read'),
    path('clear/', views.clear_chat_history, name='clear_history'),
    # Admin endpoints and purchase
    path('admin/send/', views.admin_send_message, name='admin_send'),
    path('admin/mark-read/', views.mark_admin_read, name='mark_admin_read'),
    path('purchase/write/', views.purchase_write_permission, name='purchase_write'),
    # Support tickets
    path('tickets/', views.support_tickets, name='tickets'),
    path('tickets/create/', views.create_ticket, name='create_ticket'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:ticket_id>/reply/', views.ticket_reply, name='ticket_reply'),
    path('tickets/<int:ticket_id>/status/', views.update_ticket_status, name='update_status'),
]