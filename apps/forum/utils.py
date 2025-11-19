"""
Утилиты для обработки контента форума с поддержкой маркдауна и подсветки кода
"""

import re
from html import escape

def highlight_code(code, language='plaintext'):
    """Подсветка синтаксиса кода (упрощённая версия)"""
    # Базовая подсветка для Python, JavaScript, SQL и т.д.
    keywords = {
        'python': ['def', 'class', 'import', 'from', 'return', 'if', 'else', 'for', 'while', 'True', 'False', 'None'],
        'javascript': ['function', 'const', 'let', 'var', 'return', 'if', 'else', 'for', 'while', 'true', 'false', 'null'],
        'sql': ['SELECT', 'FROM', 'WHERE', 'JOIN', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP'],
        'html': ['html', 'head', 'body', 'div', 'span', 'p', 'a', 'img', 'script', 'style'],
    }
    
    # Простой парсинг - можно расширить с помощью pygments или других библиотек
    lines = code.split('\n')
    highlighted = []
    
    for line in lines:
        highlighted_line = escape(line)
        highlighted.append(highlighted_line)
    
    return '\n'.join(highlighted)

def process_content(content):
    """Обработка контента с поддержкой маркдауна и кодовых блоков"""
    
    # Экранируем HTML теги по умолчанию, кроме разрешённых
    content = escape(content)
    
    # Преобразуем маркдаун код (```язык ... ```) в красивые блоки
    def replace_code_block(match):
        language = match.group(1) or 'plaintext'
        code = match.group(2)
        highlighted = highlight_code(code, language)
        
        return f'''<div class="code-block language-{language}">
            <div class="code-header">
                <span class="language-label">{language.upper()}</span>
                <button class="copy-btn" onclick="copyCode(this)">📋 Копировать</button>
            </div>
            <pre><code class="code-content">{highlighted}</code></pre>
        </div>'''
    
    # Заменяем блоки кода
    content = re.sub(
        r'```([\w]*)\n(.*?)```',
        replace_code_block,
        content,
        flags=re.DOTALL
    )
    
    # Преобразуем inline код
    content = re.sub(
        r'`([^`]+)`',
        r'<code class="inline-code">\1</code>',
        content
    )
    
    # Преобразуем простое маркдаун форматирование
    # Жирный текст **текст** или __текст__
    content = re.sub(
        r'\*\*(.+?)\*\*',
        r'<strong>\1</strong>',
        content
    )
    content = re.sub(
        r'__(.+?)__',
        r'<strong>\1</strong>',
        content
    )
    
    # Наклонный текст *текст* или _текст_
    content = re.sub(
        r'\*([^*]+)\*',
        r'<em>\1</em>',
        content
    )
    content = re.sub(
        r'_([^_]+)_',
        r'<em>\1</em>',
        content
    )
    
    # Линии разделения
    content = re.sub(
        r'^---+$',
        '<hr class="content-divider">',
        content,
        flags=re.MULTILINE
    )
    
    # Заголовки # # ## ### и т.д.
    content = re.sub(
        r'^##### (.*?)$',
        r'<h5 class="content-heading-5">\1</h5>',
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r'^#### (.*?)$',
        r'<h4 class="content-heading-4">\1</h4>',
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r'^### (.*?)$',
        r'<h3 class="content-heading-3">\1</h3>',
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r'^## (.*?)$',
        r'<h2 class="content-heading-2">\1</h2>',
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r'^# (.*?)$',
        r'<h1 class="content-heading-1">\1</h1>',
        content,
        flags=re.MULTILINE
    )
    
    # Списки
    # Неупорядоченный список
    content = re.sub(
        r'^\* (.+?)$',
        r'<li>\1</li>',
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r'^\- (.+?)$',
        r'<li>\1</li>',
        content,
        flags=re.MULTILINE
    )
    
    # Оборачиваем li в ul
    content = re.sub(
        r'(<li>.*?</li>)',
        r'<ul class="content-list">\1</ul>',
        content,
        flags=re.DOTALL
    )
    
    # Цитаты > текст
    content = re.sub(
        r'^> (.+?)$',
        r'<blockquote class="content-quote">\1</blockquote>',
        content,
        flags=re.MULTILINE
    )
    
    # Преобразуем URL в ссылки (если они не в HTML тегах)
    content = re.sub(
        r'(?<!href=["\'])(https?://[^\s<>]+)',
        r'<a href="\1" target="_blank" class="content-link">\1</a>',
        content
    )
    
    # Преобразуем переносы строк в <br>
    content = content.replace('\n\n', '</p><p class="content-paragraph">')
    content = f'<p class="content-paragraph">{content}</p>'
    
    return content

def render_forum_content(content):
    """Основной метод для рендеринга контента форума"""
    return process_content(content)
