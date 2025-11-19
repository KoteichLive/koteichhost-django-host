import requests
import urllib3
import base64

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_connection():
    base_url = "https://koteichcatalog.ru/ollama"
    username = "ollama"
    password = "secret123"
    
    # Создаем заголовки аутентификации
    auth_string = f"{username}:{password}"
    auth_bytes = auth_string.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {base64_auth}'
    }
    
    print("🔍 Тестирование подключения к Ollama...")
    print(f"📍 URL: {base_url}")
    print(f"📍 Логин: {username}")
    
    # Тестируем разные endpoints
    endpoints = [
        "/api/tags",
        "/api/version", 
        "/"
    ]
    
    for endpoint in endpoints:
        try:
            url = base_url + endpoint
            print(f"\n🔧 Пробуем: {url}")
            
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            print(f"📍 Статус: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Успешно!")
                if endpoint == "/api/tags":
                    print(f"📍 Ответ: {response.text[:200]}...")
                else:
                    print(f"📍 Ответ: {response.text}")
            else:
                print(f"❌ Ошибка: {response.text}")
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Ошибка подключения: {e}")
        except requests.exceptions.Timeout:
            print("❌ Таймаут")
        except Exception as e:
            print(f"❌ Другая ошибка: {e}")

if __name__ == "__main__":
    test_connection()