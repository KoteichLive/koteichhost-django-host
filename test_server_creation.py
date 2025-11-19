#!/usr/bin/env python
"""
Тестирование создания сервера
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koteich.settings')
django.setup()

from apps.servers.api_client import ServerAPIClient
from apps.servers.models import ServerType, CasePlan, ServerCase, ServerPlan
from apps.accounts.models import CustomUser
import logging

# Включаем логирование в консоль
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_server_creation():
    """Тест создания сервера"""
    print("\n" + "="*60)
    print("ТЕСТ СОЗДАНИЯ СЕРВЕРА")
    print("="*60 + "\n")
    
    # Получаем пользователя
    user = CustomUser.objects.first()
    if not user:
        print("❌ Нет пользователей в БД")
        return
    
    print(f"✓ Используем пользователя: {user.username} (ID: {user.id})")
    
    # Получаем тип сервера
    server_type = ServerType.objects.filter(is_active=True).first()
    if not server_type:
        print("❌ Нет активных типов серверов")
        return
    
    print(f"✓ Используем тип сервера: {server_type.title} (mod_id: {server_type.mod_id})")
    
    # Получаем план
    plan = ServerPlan.objects.filter(server_type=server_type, is_active=True).first()
    if not plan:
        print("❌ Нет активных планов для этого типа")
        return
    
    print(f"✓ Используем план: {plan.name} ({plan.slots} слотов)")
    
    # Готовим данные для создания
    server_data = {
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'name': f'test_server_{user.id}',
        'mod': server_type.mod_id,
        'slots': plan.slots,
        'plan': plan.name
    }
    
    print(f"\n📋 Данные для создания:")
    for key, value in server_data.items():
        print(f"  {key}: {value} (тип: {type(value).__name__})")
    
    # Пытаемся создать сервер
    print(f"\n🔄 Создаем сервер...")
    api_client = ServerAPIClient()
    
    result = api_client.create_server(server_data)
    
    if result:
        print(f"\n✅ УСПЕШНО СОЗДАН!")
        print(f"  ID: {result.get('id')}")
        print(f"  Имя: {result.get('name')}")
        print(f"  IP: {result.get('ip')}")
        print(f"  Порт: {result.get('port')}")
    else:
        print(f"\n❌ ОШИБКА СОЗДАНИЯ")
        print("Смотрите логи выше для подробностей")

if __name__ == '__main__':
    test_server_creation()
