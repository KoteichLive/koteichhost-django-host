# apps/servers/api_client.py
import requests
import logging
from django.conf import settings
from .gameap_client import GameAPClient

logger = logging.getLogger(__name__)

class ServerAPIClient:
    """
    Основной клиент для работы с GameAP
    Заменяет старый FastAPI + Docker клиент
    """
    
    def __init__(self):
        self.gameap_client = GameAPClient()
    
    def check_health(self):
        return self.gameap_client.check_health()
    
    def get_user_servers(self, user_id):
        return self.gameap_client.get_user_servers(user_id)
    
    def create_server(self, server_data):
        return self.gameap_client.create_server(server_data)
    
    def start_server(self, server_id, user_id):
        return self.gameap_client.start_server(server_id, user_id)
    
    def stop_server(self, server_id, user_id):
        return self.gameap_client.stop_server(server_id, user_id)
    
    def restart_server(self, server_id, user_id):
        return self.gameap_client.restart_server(server_id, user_id)
    
    def get_server_status(self, server_id, user_id):
        return self.gameap_client.get_server_status(server_id, user_id)
    
    def delete_server(self, server_id, user_id):
        return self.gameap_client.delete_server(server_id, user_id)
    
    def get_monitoring_data(self, user_id=None):
        """Получение данных мониторинга"""
        try:
            if user_id:
                servers = self.get_user_servers(user_id)
            else:
                servers = self.gameap_client.get_all_servers()
            
            monitoring_data = []
            for server in servers:
                status = self.get_server_status(server['id'], user_id or 'system')
                server_data = {
                    'id': server['id'],
                    'name': server['name'],
                    'status': status,
                    'mod': server.get('mod', 'unknown'),
                    'ip': server.get('ip', '0.0.0.0'),
                    'port': server.get('port', 0),
                    'slots': server.get('slots', 0),
                    'online': status.get('online', 0) if status else 0,
                    'plan': server.get('plan', 'basic')
                }
                monitoring_data.append(server_data)
            
            return monitoring_data
        except Exception as e:
            print(f"Error getting monitoring data: {e}")
            return []

class OllamaAPIClient:
    """
    Клиент для работы с нейросетью Ollama
    """
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.auth = (settings.OLLAMA_USERNAME, settings.OLLAMA_PASSWORD)
    
    def check_health(self):
        """Проверка доступности нейросети"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                auth=self.auth,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    def generate_response(self, prompt, model=None):
        """Генерация ответа от нейросети"""
        try:
            if model is None:
                model = settings.DEFAULT_MODEL
                
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                auth=self.auth,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            return None
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None