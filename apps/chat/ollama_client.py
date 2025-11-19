import requests
import urllib3
import base64
import json
from django.conf import settings
from .knowledge_service import KnowledgeService

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OllamaClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip('/')
        self.auth = (settings.OLLAMA_USERNAME, settings.OLLAMA_PASSWORD)
        self.model = settings.DEFAULT_MODEL
        self.timeout = getattr(settings, 'OLLAMA_TIMEOUT', 120)  # Таймаут по умолчанию 120 сек
    
    def get_auth_headers(self):
        """Создание заголовков для аутентификации"""
        try:
            auth_string = f"{self.auth[0]}:{self.auth[1]}"
            auth_bytes = auth_string.encode('ascii')
            base64_auth = base64.b64encode(auth_bytes).decode('ascii')
            
            return {
                'Content-Type': 'application/json',
                'Authorization': f'Basic {base64_auth}'
            }
        except Exception as e:
            print(f"❌ Ошибка при создании заголовков аутентификации: {e}")
            return {'Content-Type': 'application/json'}
    
    def build_prompt(self, message, username=None):
        """Создание промпта с контекстом базы знаний"""
        try:
            # Получаем базовую информацию о компании
            company_info = KnowledgeService.get_company_info()
            
            # Получаем всю базу знаний для контекста
            knowledge_base = KnowledgeService.get_all_knowledge()
            
            # Проверяем есть ли точный ответ в базе знаний
            exact_answer = KnowledgeService.find_answer(message)
            
            base_prompt = f"""Ты - AI ассистент компании Koteich. Отвечай вежливо и профессионально на русском языке.

ИНФОРМАЦИЯ О КОМПАНИИ:
{company_info}

БАЗА ЗНАНИЙ ДЛЯ ОТВЕТОВ:
{knowledge_base}

Пользователь {username if username else 'гость'} спрашивает: "{message}"

"""
            if exact_answer:
                base_prompt += f"""
ВАЖНО: Найден точный ответ в базе знаний: "{exact_answer}"
Используй эту информацию для формирования ответа, но не копируй дословно. 
Ответь естественно и развернуто на основе этой информации.

Ответ:
"""
            else:
                base_prompt += """
Ответь на вопрос пользователя. Если информация отсутствует в базе знаний, 
вежливо сообщи об этом и предложи обратиться к администратору.

Ответ:
"""
            
            return base_prompt
        except Exception as e:
            print(f"❌ Ошибка при создании промпта: {e}")
            return f"Ответь на вопрос пользователя: {message}\n\nОтвет:"
    
    def send_message(self, message, username=None):
        """Отправить сообщение в Ollama и получить ответ"""
        try:
            # Проверяем, доступен ли сервис перед отправкой
            if not self._check_connection():
                print("❌ Невозможно подключиться к серверу Ollama")
                return {
                    'success': False,
                    'error': 'Сервер Ollama недоступен',
                    'response': 'Сервис AI временно недоступен. Попробуйте позже.'
                }
            
            # Проверяем базу знаний
            knowledge_answer = KnowledgeService.find_answer(message)
            
            headers = self.get_auth_headers()
            
            # Создаем промпт с контекстом
            prompt = self.build_prompt(message, username)
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_predict": 500  # Ограничиваем длину ответа
                }
            }
            
            print(f"🔧 Отправка запроса к: {self.base_url}/api/generate")
            print(f"🔧 Модель: {self.model}")
            print(f"🔧 Таймаут: {self.timeout} сек")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                headers=headers,
                json=payload,
                verify=False,
                timeout=self.timeout
            )
            
            print(f"🔧 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    ai_response = response_data.get('response', '').strip()
                    
                    if not ai_response:
                        ai_response = 'Извините, не смог сгенерировать ответ. Попробуйте переформулировать вопрос.'
                    
                    print(f"✅ Успешный ответ от API (длина: {len(ai_response)} символов)")
                    
                    return {
                        'success': True,
                        'response': ai_response,
                        'model': response_data.get('model', self.model),
                        'used_knowledge_base': knowledge_answer is not None
                    }
                except json.JSONDecodeError as e:
                    print(f"❌ Ошибка при парсинге JSON: {e}")
                    return {
                        'success': False,
                        'error': f"Ошибка парсинга ответа API",
                        'response': 'Ошибка обработки ответа сервера'
                    }
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                print(f"Ответ: {response.text[:200]}")
                
                error_msg = 'Неизвестная ошибка'
                if response.status_code == 401:
                    error_msg = 'Ошибка аутентификации'
                elif response.status_code == 404:
                    error_msg = 'Модель не найдена'
                elif response.status_code == 503:
                    error_msg = 'Сервис недоступен'
                
                return {
                    'success': False,
                    'error': f"Ошибка API Ollama: {response.status_code}",
                    'response': f'Ошибка подключения к AI сервису: {error_msg}'
                }
                
        except requests.exceptions.Timeout:
            print(f"❌ Таймаут при подключении к Ollama (ждали {self.timeout} сек)")
            return {
                'success': False,
                'error': 'Таймаут при подключении к Ollama',
                'response': 'Сервис AI слишком долго обрабатывает запрос. Попробуйте позже.'
            }
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Ошибка подключения к Ollama: {e}")
            return {
                'success': False,
                'error': f'Не удалось подключиться к серверу Ollama',
                'response': 'Сервер Ollama недоступен. Попробуйте позже.'
            }
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f"Неожиданная ошибка: {str(e)}",
                'response': 'Произошла непредвиденная ошибка обработки запроса.'
            }
    
    def _check_connection(self):
        """Проверить доступность сервера Ollama"""
        try:
            headers = self.get_auth_headers()
            response = requests.get(
                f"{self.base_url}/api/tags",
                headers=headers,
                timeout=5,
                verify=False
            )
            return response.status_code == 200
        except:
            return False
    
    def get_available_models(self):
        """Получение списка доступных моделей"""
        try:
            headers = self.get_auth_headers()
            response = requests.get(
                f"{self.base_url}/api/tags",
                headers=headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                print(f"✅ Получено {len(models)} моделей из Ollama")
                return models
            else:
                print(f"❌ Ошибка получения моделей: {response.status_code}")
            return []
        except Exception as e:
            print(f"❌ Ошибка получения списка моделей: {e}")
            return []
