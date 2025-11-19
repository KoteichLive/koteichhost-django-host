# forum/forms.py (дополнение)
from django import forms
from .models import Topic, Post, Category

class TopicForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'beautiful-select'}),
        label="Категория",
        empty_label="Выберите категорию"
    )
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'beautiful-input',
            'placeholder': 'Введите заголовок темы'
        }),
        label="Заголовок"
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'beautiful-textarea',
            'placeholder': 'Введите содержание первого сообщения',
            'rows': 8
        }),
        label="Содержание сообщения"
    )
    
    class Meta:
        model = Topic
        fields = ['category', 'title', 'content']

class PostForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'beautiful-textarea',
            'placeholder': 'Введите ваше сообщение...',
            'rows': 6
        }),
        label="Сообщение"
    )
    
    class Meta:
        model = Post
        fields = ['content']

class PostEditForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'beautiful-textarea',
            'rows': 8
        }),
        label="Содержание"
    )
    reason = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'beautiful-input',
            'placeholder': 'Причина редактирования (необязательно)'
        }),
        label="Причина редактирования",
        max_length=200
    )
    
    class Meta:
        model = Post
        fields = ['content', 'reason']