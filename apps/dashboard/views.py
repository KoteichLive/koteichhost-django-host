# apps/dashboard/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.core.cache import cache
from apps.servers.api_client import ServerAPIClient
import logging

logger = logging.getLogger(__name__)

@login_required
def dashboard(request):
    """Главная панель управления"""
    api_client = ServerAPIClient()
    
    # Получаем серверы пользователя
    try:
        user_servers = api_client.get_user_servers(request.user.id)
        
        # Получаем статус для каждого сервера
        servers_with_status = []
        for server in user_servers:
            status = api_client.get_server_status(server['id'], request.user.id)
            server['status'] = status.get('status', 'unknown') if status else 'unknown'
            server['process_active'] = status.get('process_active', False) if status else False
            server['online_players'] = status.get('online', 0) if status else 0
            server['address'] = f"{server.get('ip', '0.0.0.0')}:{server.get('port', 0)}"
            server['on_auction'] = False  # Заглушка, можно интегрировать с аукционом
            
            servers_with_status.append(server)
            
    except Exception as e:
        logger.error(f"Error getting user servers for dashboard: {e}")
        servers_with_status = []
    
    # Статистика
    total_servers = len(servers_with_status)
    online_servers = len([s for s in servers_with_status if s.get('process_active')])
    total_players = sum([s.get('online_players', 0) for s in servers_with_status])
    
    context = {
        'user': request.user,
        'servers': servers_with_status,
        'user_balance': getattr(request.user, 'balance', 0),
        'total_servers': total_servers,
        'online_servers': online_servers,
        'total_players': total_players,
    }
    return render(request, 'dashboard/statistics.html', context)

@login_required
def get_servers_data(request):
    """API endpoint для получения данных серверов (AJAX)"""
    api_client = ServerAPIClient()
    
    try:
        user_servers = api_client.get_user_servers(request.user.id)
        
        # Форматируем данные для фронтенда
        servers_data = []
        for server in user_servers:
            status = api_client.get_server_status(server['id'], request.user.id)
            
            server_data = {
                'id': server['id'],
                'name': server.get('name', 'Без названия'),
                'mod': server.get('mod', 'Не указан'),
                'slots': server.get('slots', 0),
                'status': status.get('status', 'unknown') if status else 'unknown',
                'process_active': status.get('process_active', False) if status else False,
                'online_players': status.get('online', 0) if status else 0,
                'address': f"{server.get('ip', '0.0.0.0')}:{server.get('port', 0)}",
                'on_auction': False,
                'cpu_usage': status.get('cpu_usage', 0),
                'memory_usage': status.get('memory_usage', 0),
                'uptime_percent': calculate_uptime_percent(status),
            }
            servers_data.append(server_data)
        
        return JsonResponse(servers_data, safe=False)
        
    except Exception as e:
        logger.error(f"API error in get_servers_data: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# Вспомогательные функции
def calculate_uptime_percent(status):
    """Рассчитывает процент аптайма сервера"""
    if not status:
        return 0
    
    # Простая логика - если процесс активен, считаем 100% аптайм
    # В реальном приложении здесь должна быть сложная логика
    return 100 if status.get('process_active') else 0

@login_required
def extend_server(request, server_id):
    """Продление сервера"""
    if request.method == 'POST':
        try:
            # Здесь должна быть логика продления сервера
            # Пока заглушка
            return JsonResponse({
                'success': True,
                'message': 'Сервер успешно продлен'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def put_on_auction(request, server_id):
    """Выставление сервера на аукцион"""
    if request.method == 'POST':
        try:
            # Здесь должна быть логика аукциона
            # Пока заглушка
            return JsonResponse({
                'success': True,
                'message': 'Сервер выставлен на аукцион'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)