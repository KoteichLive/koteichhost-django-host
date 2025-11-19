from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import json
import threading
from .ollama_client import OllamaClient
from .models import ChatMessage, SupportTicket, TicketReply
from .models import ChatAdminMessage, ChatRestriction
from django.contrib.auth import get_user_model
import time
from django.utils import timezone
from decimal import Decimal
from django.contrib import messages as django_messages

User = get_user_model()

def process_ai_response(message_id, message_text, username):
    """Фоновая обработка AI ответа"""
    try:
        client = OllamaClient()
        result = client.send_message(message_text, username)
        
        # Обновляем сообщение в базе данных
        chat_message = ChatMessage.objects.get(id=message_id)
        if result['success']:
            chat_message.response = result['response']
        else:
            chat_message.response = f"Ошибка: {result.get('error', 'Неизвестная ошибка')}"
        chat_message.save()
        
    except Exception as e:
        print(f"Error processing AI response: {e}")

@login_required
def chat_view(request):
    """Основное представление чата"""
    client = OllamaClient()
    
    # Получаем список доступных моделей
    try:
        available_models = client.get_available_models()
    except Exception as e:
        print(f"Error getting available models: {e}")
        available_models = []
    
    # Получаем список пользователей для личных сообщений
    users = User.objects.exclude(id=request.user.id).values('id', 'username')[:20]
    
    # Получаем список собеседников с последними сообщениями
    chat_partners = []
    
    try:
        # Получаем отправленные сообщения
        sent_messages = ChatMessage.objects.filter(
            user=request.user, 
            message_type='user'
        ).select_related('recipient')
        
        # Получаем полученные сообщения
        received_messages = ChatMessage.objects.filter(
            recipient=request.user, 
            message_type='user'
        ).select_related('user')
        
        # Собираем всех уникальных собеседников
        partners_dict = {}
        
        # Обрабатываем отправленные сообщения
        for msg in sent_messages:
            if msg.recipient:
                partner_id = msg.recipient.id
                if partner_id not in partners_dict:
                    partners_dict[partner_id] = {
                        'id': partner_id,
                        'username': msg.recipient.username,
                        'last_message': msg.message,
                        'timestamp': msg.created_at,
                        'unread_count': 0
                    }
                else:
                    if msg.created_at > partners_dict[partner_id]['timestamp']:
                        partners_dict[partner_id]['last_message'] = msg.message
                        partners_dict[partner_id]['timestamp'] = msg.created_at
        
        # Обрабатываем полученные сообщения
        for msg in received_messages:
            partner_id = msg.user.id
            unread_count = ChatMessage.objects.filter(
                user_id=partner_id,
                recipient=request.user,
                message_type='user',
                is_read=False
            ).count()
            
            if partner_id not in partners_dict:
                partners_dict[partner_id] = {
                    'id': partner_id,
                    'username': msg.user.username,
                    'last_message': msg.message,
                    'timestamp': msg.created_at,
                    'unread_count': unread_count
                }
            else:
                if msg.created_at > partners_dict[partner_id]['timestamp']:
                    partners_dict[partner_id]['last_message'] = msg.message
                    partners_dict[partner_id]['timestamp'] = msg.created_at
                partners_dict[partner_id]['unread_count'] = unread_count
        
        # Преобразуем в список и сортируем
        chat_partners = sorted(
            list(partners_dict.values()), 
            key=lambda x: x['timestamp'], 
            reverse=True
        )
        
    except Exception as e:
        print(f"Error loading chat partners: {e}")
        chat_partners = []
    
    # Для админов добавляем информацию о непрочитанных тикетах
    unread_tickets_count = 0
    if request.user.is_staff:
        unread_tickets_count = SupportTicket.objects.filter(is_read=False).count()
    
    context = {
        'default_model': client.model,
        'available_models': available_models,
        'users': list(users),
        'chat_partners': chat_partners,
        'admin_unread_count': ChatAdminMessage.objects.filter(user=request.user, is_read=False).count(),
        'unread_tickets_count': unread_tickets_count
    }
    return render(request, 'chat/chat.html', context)

@login_required
@csrf_exempt
def send_message(request):
    """Отправка сообщения (AI или пользователю)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            message_type = data.get('type', 'ai')
            recipient_username = data.get('recipient', '').strip()
            
            if not message:
                return JsonResponse({'error': 'Пустое сообщение'}, status=400)
            
            if message_type == 'user':
                # Проверяем ограничения пользователя (нельзя писать)
                restriction = getattr(request.user, 'chat_restriction', None)
                if restriction and restriction.is_active() and restriction.restricted_write:
                    # Если можно выкупить — возвращаем цену
                    resp = {'error': 'restricted', 'message': 'Вам запрещено отправлять сообщения', 'purchasable': restriction.purchasable}
                    if restriction.purchasable and restriction.price:
                        resp['price'] = str(restriction.price)
                    return JsonResponse(resp, status=403)
                # Отправка пользователю (синхронно)
                try:
                    # Сообщение администрации: если recipient_username пустой или равен 'admin'
                    if not recipient_username or recipient_username.lower() in ['admin', '__admin__']:
                        chat_message = ChatMessage.objects.create(
                            user=request.user,
                            recipient=None,
                            message=message,
                            message_type='user'
                        )
                        
                        # Создаем тикет техподдержки для администраторов
                        ticket = SupportTicket.objects.create(
                            user=request.user,
                            subject=message[:100] if len(message) >= 100 else message,
                            message=message,
                            status='new',
                            priority='medium'
                        )
                        
                    else:
                        recipient = User.objects.get(username=recipient_username)
                        if recipient == request.user:
                            return JsonResponse({'error': 'Нельзя отправить сообщение самому себе'}, status=400)

                        chat_message = ChatMessage.objects.create(
                            user=request.user,
                            recipient=recipient,
                            message=message,
                            message_type='user'
                        )

                    return JsonResponse({
                        'success': True,
                        'message_id': chat_message.id,
                        'timestamp': chat_message.created_at.isoformat(),
                        'type': 'user',
                        'sender': request.user.username
                    })

                except User.DoesNotExist:
                    return JsonResponse({'error': 'Пользователь не найден'}, status=404)
            
            else:
                # Отправка в AI (асинхронно)
                chat_message = ChatMessage.objects.create(
                    user=request.user,
                    message=message,
                    response='',
                    message_type='ai'
                )
                
                # Запускаем фоновую обработку
                thread = threading.Thread(
                    target=process_ai_response,
                    args=(chat_message.id, message, request.user.username)
                )
                thread.daemon = True
                thread.start()
                
                return JsonResponse({
                    'success': True,
                    'message_id': chat_message.id,
                    'timestamp': chat_message.created_at.isoformat(),
                    'type': 'ai',
                    'immediate_response': True
                })
                    
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Ошибка сервера: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Метод не разрешен'}, status=405)


@login_required
@csrf_exempt
def admin_send_message(request):
    """Admin sends a message to a user (creates ChatAdminMessage)."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)

    try:
        data = json.loads(request.body)
        recipient_username = data.get('recipient', '').strip()
        content = data.get('content', '').strip()
        if not recipient_username or not content:
            return JsonResponse({'error': 'Недостаточно данных'}, status=400)

        recipient = get_object_or_404(User, username=recipient_username)
        msg = ChatAdminMessage.objects.create(user=recipient, admin=request.user, content=content)
        return JsonResponse({'success': True, 'id': msg.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def mark_admin_read(request):
    """Mark all admin messages for current user as read."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)

    try:
        ChatAdminMessage.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@csrf_exempt
def purchase_write_permission(request):
    """User purchases write permission if restriction is purchasable."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)

    try:
        data = json.loads(request.body)
        restriction = getattr(request.user, 'chat_restriction', None)
        if not restriction or not restriction.is_active() or not restriction.purchasable:
            return JsonResponse({'error': 'Нет доступного ограничения для выкупа'}, status=400)

        price = restriction.price or Decimal('0')
        # Проверяем баланс у пользователя
        bal = getattr(request.user, 'balance', None)
        if bal is None:
            return JsonResponse({'error': 'Баланс пользователя не найден'}, status=500)

        if Decimal(bal) < Decimal(price):
            return JsonResponse({'error': 'Недостаточно средств'}, status=402)

        # Списываем средства и снимаем ограничение
        request.user.balance = Decimal(bal) - Decimal(price)
        request.user.save()

        restriction.restricted_write = False
        restriction.purchasable = False
        restriction.active = False
        restriction.save()

        # Оповещаем администрацию (опционально)
        ChatAdminMessage.objects.create(user=request.user, admin=None, content=f'Вы выкупили право писать за {price}₽')

        return JsonResponse({'success': True, 'new_balance': str(request.user.balance)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_chat_history(request):
    """Получение истории чата (AI + личные сообщения + админ)"""
    chat_type = request.GET.get('type', 'all')
    recipient_username = request.GET.get('recipient', '')
    last_message_id = request.GET.get('last_id', 0)
    
    try:
        if chat_type == 'ai':
            messages = ChatMessage.objects.filter(
                user=request.user, 
                message_type='ai'
            ).order_by('created_at')[:50]
        elif chat_type == 'user' and recipient_username:
            try:
                recipient = User.objects.get(username=recipient_username)
                if last_message_id and last_message_id != '0':
                    messages = ChatMessage.objects.filter(
                        Q(user=request.user, recipient=recipient, message_type='user') | 
                        Q(user=recipient, recipient=request.user, message_type='user'),
                        id__gt=int(last_message_id)
                    ).select_related('user', 'recipient').order_by('created_at')
                else:
                    messages = ChatMessage.objects.filter(
                        Q(user=request.user, recipient=recipient, message_type='user') | 
                        Q(user=recipient, recipient=request.user, message_type='user')
                    ).select_related('user', 'recipient').order_by('created_at')[:100]
            except User.DoesNotExist:
                messages = ChatMessage.objects.none()
        elif chat_type == 'admin':
            # Администрация: объединяем ChatAdminMessage и ChatMessage с recipient=None
            admin_msgs = ChatAdminMessage.objects.filter(user=request.user).order_by('created_at')
            user_admin_msgs = ChatMessage.objects.filter(user=request.user, recipient__isnull=True, message_type='user').order_by('created_at')
            combined = []
            for m in admin_msgs:
                combined.append(('admin', m))
            for m in user_admin_msgs:
                combined.append(('user_admin', m))
            combined.sort(key=lambda t: t[1].created_at)
            messages = combined
        else:
            messages = ChatMessage.objects.filter(
                Q(user=request.user) | Q(recipient=request.user)
            ).select_related('user', 'recipient').order_by('created_at')[:50]
        
        history = []
        
        # Если messages — список пар (тип, объект) для admin-чата
        if chat_type == 'admin':
            last_id = 0
            for kind, obj in messages:
                if kind == 'admin':
                    history.append({
                        'id': obj.id,
                        'sender': obj.admin.username if obj.admin else 'Администрация',
                        'message': obj.content,
                        'timestamp': obj.created_at.isoformat(),
                        'type': 'admin',
                        'is_read': obj.is_read
                    })
                    if obj.id > last_id:
                        last_id = obj.id
                else:
                    # user_admin
                    history.append({
                        'id': obj.id,
                        'sender': obj.user.username,
                        'message': obj.message,
                        'timestamp': obj.created_at.isoformat(),
                        'type': 'user_admin',
                        'is_own': True,
                        'is_read': obj.is_read
                    })
                    if obj.id > last_id:
                        last_id = obj.id
            last_id = history[-1]['id'] if history else 0
            return JsonResponse({
                'history': history,
                'last_id': last_id,
                'has_new_messages': len(history) > 0
            })
        
        # Обычные сообщения (AI, user, etc)
        for msg in messages:
            if msg.message_type == 'ai':
                history.append({
                    'id': msg.id,
                    'sender': 'user',
                    'message': msg.message,
                    'timestamp': msg.created_at.isoformat(),
                    'type': 'ai'
                })
                
                if msg.response:
                    history.append({
                        'id': msg.id,
                        'sender': 'assistant',
                        'message': msg.response,
                        'timestamp': msg.created_at.isoformat(),
                        'type': 'ai',
                        'is_ready': True
                    })
                else:
                    history.append({
                        'id': msg.id,
                        'sender': 'assistant',
                        'message': '🤔 AI думает...',
                        'timestamp': msg.created_at.isoformat(),
                        'type': 'ai',
                        'is_ready': False
                    })
            else:
                history.append({
                    'id': msg.id,
                    'sender': msg.user.username,
                    'recipient': msg.recipient.username if msg.recipient else None,
                    'message': msg.message,
                    'timestamp': msg.created_at.isoformat(),
                    'type': 'user',
                    'is_own': msg.user == request.user,
                    'is_read': msg.is_read
                })
        
        last_id = history[-1]['id'] if history else 0
        
        return JsonResponse({
            'history': history,
            'last_id': last_id,
            'has_new_messages': len(history) > 0
        })
        
    except Exception as e:
        return JsonResponse({'history': [], 'error': str(e), 'last_id': 0})


@login_required
@csrf_exempt
def check_new_messages(request):
    """Быстрая проверка новых сообщений"""
    try:
        last_message_id = request.GET.get('last_id', 0)
        recipient_username = request.GET.get('recipient', '')
        
        if not recipient_username or not last_message_id:
            return JsonResponse({'has_new': False, 'last_id': last_message_id})
        
        recipient = User.objects.get(username=recipient_username)
        
        # Проверяем есть ли новые сообщения от этого пользователя
        new_messages_count = ChatMessage.objects.filter(
            user=recipient,
            recipient=request.user,
            message_type='user',
            id__gt=int(last_message_id)
        ).count()
        
        return JsonResponse({
            'has_new': new_messages_count > 0,
            'last_id': last_message_id
        })
        
    except Exception as e:
        return JsonResponse({'has_new': False, 'last_id': last_message_id})


@login_required
def get_users_list(request):
    """Получение списка пользователей для чата"""
    try:
        users = User.objects.exclude(id=request.user.id).values('id', 'username', 'email')[:50]
        return JsonResponse({'users': list(users)})
    except:
        return JsonResponse({'users': []})


@login_required
@csrf_exempt
def mark_as_read(request):
    """Пометить сообщения как прочитанные"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            recipient_username = data.get('recipient', '')
            
            if recipient_username:
                recipient = User.objects.get(username=recipient_username)
                ChatMessage.objects.filter(
                    user=recipient,
                    recipient=request.user,
                    message_type='user',
                    is_read=False
                ).update(is_read=True)
            
            return JsonResponse({'success': True})
        except:
            return JsonResponse({'success': False})
    return JsonResponse({'error': 'Метод не разрешен'}, status=405)

@login_required
@csrf_exempt
def clear_chat_history(request):
    """Очистка истории чата"""
    chat_type = request.GET.get('type', 'ai')
    recipient_username = request.GET.get('recipient', '')
    
    try:
        if chat_type == 'ai':
            ChatMessage.objects.filter(user=request.user, message_type='ai').delete()
        elif chat_type == 'user' and recipient_username:
            recipient = User.objects.get(username=recipient_username)
            ChatMessage.objects.filter(
                Q(user=request.user, recipient=recipient) | 
                Q(user=recipient, recipient=request.user)
            ).delete()
        
        return JsonResponse({'success': True})
    except:
        return JsonResponse({'success': False})


@login_required
def support_tickets(request):
    """Список тикетов техподдержки (для администраторов и пользователей)"""
    # Пользователи видят только свои тикеты, администраторы видят все
    if request.user.is_staff:
        tickets_qs = SupportTicket.objects.select_related('user', 'assigned_to')
    else:
        tickets_qs = SupportTicket.objects.filter(user=request.user).select_related('assigned_to')
    
    # Фильтруем по статусу
    status = request.GET.get('status', 'new')
    if status == 'all':
        tickets = tickets_qs.order_by('-created_at')
    else:
        tickets = tickets_qs.filter(status=status).order_by('-created_at')
    
    # Подсчитываем непрочитанные (только для администраторов)
    unread_count = 0
    if request.user.is_staff:
        unread_count = SupportTicket.objects.filter(is_read=False).count()
        # Отмечаем как прочитанные при просмотре списка
        SupportTicket.objects.filter(is_read=False).update(is_read=True)
    
    return render(request, 'chat/support_tickets.html', {
        'tickets': tickets,
        'status': status,
        'unread_count': unread_count,
        'is_admin': request.user.is_staff
    })


@login_required
def create_ticket(request):
    """Создать новый тикет техподдержки"""
    if request.method == 'POST':
        try:
            subject = request.POST.get('subject', '').strip()
            message = request.POST.get('message', '').strip()
            priority = request.POST.get('priority', 'medium').strip()
            
            if not subject or not message:
                django_messages.error(request, 'Заполните все поля')
                return redirect('chat:tickets')
            
            if priority not in [p[0] for p in SupportTicket.PRIORITY_CHOICES]:
                priority = 'medium'
            
            # Создаём тикет
            ticket = SupportTicket.objects.create(
                user=request.user,
                subject=subject,
                message=message,
                priority=priority,
                status='new'
            )
            
            django_messages.success(request, f'Тикет #{ticket.id} создан успешно!')
            return redirect('chat:ticket_detail', ticket_id=ticket.id)
        except Exception as e:
            django_messages.error(request, f'Ошибка: {str(e)}')
            return redirect('chat:tickets')
    
    return render(request, 'chat/create_ticket.html')


@login_required
def ticket_detail(request, ticket_id):
    """Детали конкретного тикета"""
    ticket = get_object_or_404(SupportTicket, id=ticket_id)

    # Проверка прав доступа
    if not request.user.is_staff and request.user != ticket.user:
        django_messages.error(request, 'Доступ запрещён.')
        return redirect('chat:chat')

    # Отмечаем как прочитанное
    if not ticket.is_read:
        ticket.is_read = True
        ticket.save()

    # Получаем ответы
    replies = ticket.replies.select_related('author').all()

    # Отмечаем все ответы как прочитанные для текущего пользователя
    for reply in replies:
        if not reply.is_read and reply.author != request.user:
            reply.is_read = True
            reply.save()

    return render(request, 'chat/ticket_detail.html', {
        'ticket': ticket,
        'replies': replies
    })


@login_required
@csrf_exempt
def ticket_reply(request, ticket_id):
    """Добавить ответ в тикет"""
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    
    # Проверка прав доступа
    if not request.user.is_staff and request.user != ticket.user:
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            content = data.get('content', '').strip()
            
            if not content:
                return JsonResponse({'error': 'Пустой ответ'}, status=400)
            
            reply = TicketReply.objects.create(
                ticket=ticket,
                author=request.user,
                content=content
            )
            
            # Если это ответ администратора, отмечаем тикет как в процессе
            if request.user.is_staff:
                if ticket.status == 'new':
                    ticket.status = 'in_progress'
                    ticket.save()
            
            return JsonResponse({
                'success': True,
                'reply_id': reply.id,
                'author': reply.author.username,
                'created_at': reply.created_at.isoformat()
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Метод не разрешен'}, status=405)


@login_required
@csrf_exempt
def update_ticket_status(request, ticket_id):
    """Обновить статус тикета (только для администраторов)"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status', '').strip()
            
            if new_status not in [s[0] for s in SupportTicket.STATUS_CHOICES]:
                return JsonResponse({'error': 'Неверный статус'}, status=400)
            
            ticket.status = new_status
            ticket.save()
            
            return JsonResponse({
                'success': True,
                'status': ticket.get_status_display()
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Метод не разрешен'}, status=405)

