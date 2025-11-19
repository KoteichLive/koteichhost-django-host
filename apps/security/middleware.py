import re
from django.http import HttpResponseForbidden, HttpResponse
from django.conf import settings

class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Паттерны для блокировки
        self.blocked_paths = [
            r'^/xmlrpc\.php',
            r'^/wp-',
            r'^/administrator',
            r'^/phpmyadmin',
            r'^/\.env',
            r'^/\.git',
            r'^/\.ht',
        ]
        self.blocked_user_agents = [
            'scan', 'bot', 'crawler', 'spider', 'wget', 'curl',
            'nmap', 'sqlmap', 'acunetix', 'nikto'
        ]

    def __call__(self, request):
        # Проверка пути
        path = request.path
        for pattern in self.blocked_paths:
            if re.match(pattern, path, re.IGNORECASE):
                return HttpResponse('Not Found', status=404)
        
        # Проверка User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        for blocked_ua in self.blocked_user_agents:
            if blocked_ua in user_agent:
                return HttpResponse('Access Denied', status=403)
        
        response = self.get_response(request)
        
        # Добавляем security headers
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response