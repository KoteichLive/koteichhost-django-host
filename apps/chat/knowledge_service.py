import re
from django.db.models import Q
from .models import KnowledgeBase

class KnowledgeService:
    @staticmethod
    def find_answer(user_message):
        """Поиск ответа в базе знаний"""
        message_lower = user_message.lower().strip()
        
        # Ищем точные совпадения по ключевым словам
        exact_matches = KnowledgeBase.objects.filter(
            is_active=True,
            question__iexact=message_lower
        ).order_by('-priority')
        
        if exact_matches.exists():
            return exact_matches.first().answer
        
        # Ищем частичные совпадения
        words = re.findall(r'\w+', message_lower)
        queries = [Q(question__icontains=word) for word in words if len(word) > 2]
        
        if queries:
            query = queries[0]
            for q in queries[1:]:
                query |= q
            
            partial_matches = KnowledgeBase.objects.filter(
                query,
                is_active=True
            ).order_by('-priority')
            
            if partial_matches.exists():
                return partial_matches.first().answer
        
        return None
    
    @staticmethod
    def get_company_info():
        """Получить информацию о компании"""
        company_info = KnowledgeBase.objects.filter(
            category='about',
            is_active=True
        ).order_by('-priority')
        
        info_text = ""
        for info in company_info:
            info_text += f"{info.answer}\n\n"
        
        return info_text.strip()
    
    @staticmethod
    def get_all_knowledge():
        """Получить всю базу знаний для контекста"""
        knowledge = KnowledgeBase.objects.filter(is_active=True).order_by('category', '-priority')
        
        knowledge_text = "БАЗА ЗНАНИЙ KOTEICH:\n\n"
        current_category = ""
        
        for item in knowledge:
            if item.category != current_category:
                current_category = item.category
                knowledge_text += f"\n--- {dict(KnowledgeBase.CATEGORY_CHOICES)[item.category].upper()} ---\n"
            
            knowledge_text += f"Вопрос: {item.question}\n"
            knowledge_text += f"Ответ: {item.answer}\n\n"
        
        return knowledge_text.strip()