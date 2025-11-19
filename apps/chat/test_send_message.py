import os
import django
import sys

sys.path.append('/django/prodac')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koteich.settings')
django.setup()

from apps.chat.ollama_client import OllamaClient

def test_send():
    print("🧪 Тестирование отправки сообщения...")
    
    client = OllamaClient()
    
    # Тестовое сообщение
    result = client.send_message("Привет! Ответь коротко: как дела?")
    
    print(f"📍 Успех: {result['success']}")
    if result['success']:
        print(f"📍 Ответ: {result['response']}")
        print(f"📍 Модель: {result['model']}")
    else:
        print(f"📍 Ошибка: {result['error']}")
        print(f"📍 Ответ для пользователя: {result['response']}")

if __name__ == "__main__":
    test_send()