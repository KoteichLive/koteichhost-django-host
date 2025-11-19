# Альтернативная версия - apps/chat/management/commands/init_knowledge.py
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Initialize knowledge base with basic information'
    
    def handle(self, *args, **options):
        # Импортируем внутри функции чтобы избежать циклических импортов
        from apps.chat.models import KnowledgeBase
        
        knowledge_data = [
            {
                'question': 'koteich',
                'answer': 'Koteich - это IT компания, специализирующаяся на веб-разработке, хостинге и IT решениях. Мы создаем современные веб-приложения, предоставляем надежный хостинг и оказываем техническую поддержку.',
                'category': 'about',
                'priority': 10
            },
            # ... остальные данные
        ]
        
        created_count = 0
        for data in knowledge_data:
            obj, created = KnowledgeBase.objects.get_or_create(
                question=data['question'],
                defaults=data
            )
            if created:
                self.stdout.write(f"✅ Создано: {data['question']}")
                created_count += 1
            else:
                self.stdout.write(f"⚠️ Уже существует: {data['question']}")
        
        self.stdout.write(
            self.style.SUCCESS(f'База знаний инициализирована! Создано {created_count} записей.')
        )