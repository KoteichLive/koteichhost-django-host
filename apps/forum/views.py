# forum/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Max
from django.contrib import messages
from django.utils import timezone
from django.utils.safestring import mark_safe
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Category, Topic, Post, PostEdit, ForumRewardConfig
from .forms import TopicForm, PostForm, PostEditForm
from .utils import render_forum_content
from decimal import Decimal

def forum(request):
    """Главная страница форума со списком категорий и последними темами"""
    # Убираем фильтр is_active, так как его нет в модели
    categories = Category.objects.all().order_by('order', 'name')
    
    # Получаем последние темы с информацией о последнем сообщении
    recent_topics = Topic.objects.select_related('category', 'author').annotate(
        last_activity=Max('posts__created_at'),
        posts_count=Count('posts')
    ).order_by('-last_activity')[:10]
    
    return render(request, 'forum/forum.html', {
        'categories': categories,
        'recent_topics': recent_topics
    })

def category(request, category_id):
    """Страница категории со списком тем"""
    category = get_object_or_404(Category, id=category_id)
    
    # Темы с аннотацией количества сообщений и последней активности
    topics_list = Topic.objects.filter(category=category).select_related('author').annotate(
        posts_count=Count('posts'),
        last_activity=Max('posts__created_at')
    ).order_by('-is_pinned', '-last_activity')
    
    paginator = Paginator(topics_list, 20)
    page = request.GET.get('page')
    topics = paginator.get_page(page)
    
    return render(request, 'forum/category.html', {
        'category': category,
        'topics': topics
    })

def topic_posts(request, topic_id):
    """Страница темы с сообщениями"""
    topic = get_object_or_404(Topic.objects.select_related('category', 'author'), id=topic_id)
    
    # Если пользователь зашёл в раздел форума — считаем, что он увидел уведомления
    if request.user.is_authenticated and getattr(request.user, 'has_unseen_approved_post', False):
        request.user.has_unseen_approved_post = False
        request.user.save(update_fields=['has_unseen_approved_post'])

    # Увеличиваем счетчик просмотров
    if not request.user.is_authenticated or request.user != topic.author:
        topic.views += 1
        topic.save()
    
    # Фильтруем посты в зависимости от прав пользователя
    if request.user.is_staff:
        # Админ видит все посты
        posts_list = topic.posts.select_related('author').all()
    elif request.user.is_authenticated:
        # Обычный пользователь видит: одобренные посты + свои посты
        posts_list = topic.posts.select_related('author').filter(
            Q(status='approved') | Q(author=request.user)
        )
    else:
        # Анонимный пользователь видит только одобренные
        posts_list = topic.posts.select_related('author').filter(status='approved')
    
    paginator = Paginator(posts_list, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    post_form = PostForm()
    
    return render(request, 'forum/topic_posts.html', {
        'topic': topic,
        'posts': posts,
        'post_form': post_form
    })

@login_required
def create_topic(request):
    """Создание новой темы"""
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.author = request.user
            topic.save()
            
            # Создаем первое сообщение со статусом "pending"
            post = Post.objects.create(
                topic=topic,
                author=request.user,
                content=form.cleaned_data['content'],
                status='pending'
            )
            
            # Рассчитываем вознаграждение (но не начисляем, пока не одобрено)
            reward = post.calculate_reward()
            post.reward_amount = Decimal(str(reward))
            post.save()
            
            if request.user.is_staff:
                messages.success(request, 'Тема успешно создана!')
            else:
                messages.success(request, f'Тема успешно создана! Ожидает одобрения администратором. При одобрении вы получите вознаграждение: {reward}₽')
            
            return redirect('forum:topic_posts', topic_id=topic.id)
    else:
        form = TopicForm()
    
    return render(request, 'forum/create_topic.html', {'form': form})

@login_required
def add_post(request, topic_id):
    """Добавление сообщения в тему"""
    topic = get_object_or_404(Topic, id=topic_id)
    
    if topic.is_closed and not request.user.is_staff:
        messages.error(request, 'Эта тема закрыта для обсуждения.')
        return redirect('forum:topic_posts', topic_id=topic.id)
    
    if request.method == 'POST':
        # Не позволяем пользователю иметь более одного ожидающего поста одновременно
        if Post.objects.filter(author=request.user, status='pending').exists():
            messages.error(request, 'У вас уже есть сообщение на модерации. Дождитесь одобрения перед отправкой нового.')
            return redirect('forum:topic_posts', topic_id=topic.id)

        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.author = request.user
            post.status = 'pending'  # Устанавливаем статус на одобрение
            post.save()
            
            # Рассчитываем вознаграждение (но не начисляем)
            reward = post.calculate_reward()
            post.reward_amount = Decimal(str(reward))
            post.save()
            
            # Обновляем время последней активности темы
            topic.save()
            
            if request.user.is_staff:
                messages.success(request, 'Сообщение успешно добавлено!')
            else:
                messages.success(request, f'Сообщение отправлено на одобрение! При одобрении администратором вы получите: {reward}₽')
            
            return redirect('forum:topic_posts', topic_id=topic.id)
    
    return redirect('forum:topic_posts', topic_id=topic.id)

@login_required
def edit_post(request, post_id):
    """Редактирование сообщения"""
    post = get_object_or_404(Post.objects.select_related('topic', 'topic__category'), id=post_id)
    
    # Проверяем права на редактирование
    if not (request.user == post.author or request.user.is_staff):
        messages.error(request, 'У вас нет прав для редактирования этого сообщения.')
        return redirect('forum:topic_posts', topic_id=post.topic.id)
    
    if request.method == 'POST':
        form = PostEditForm(request.POST, instance=post)
        if form.is_valid():
            # Сохраняем старую версию в историю если контент изменился
            if post.content != form.cleaned_data['content']:
                PostEdit.objects.create(
                    post=post,
                    editor=request.user,
                    old_content=post.content,
                    new_content=form.cleaned_data['content'],
                    reason=form.cleaned_data.get('reason', '')
                )
            
            form.save()
            messages.success(request, 'Сообщение успешно отредактировано!')
            return redirect('forum:topic_posts', topic_id=post.topic.id)
    else:
        form = PostEditForm(instance=post)
    
    return render(request, 'forum/edit_post.html', {
        'form': form,
        'post': post,
        'topic': post.topic
    })

def post_history(request, post_id):
    """История правок сообщения"""
    post = get_object_or_404(Post.objects.select_related('topic', 'author'), id=post_id)
    edits = post.edits.select_related('editor').all()
    
    return render(request, 'forum/post_history.html', {
        'post': post,
        'edits': edits
    })


@login_required
def moderate_posts(request):
    """Страница модерации постов (только для админов)"""
    if not request.user.is_staff:
        messages.error(request, 'Доступ запрещён.')
        return redirect('forum:forum')
    
    pending_posts = Post.objects.filter(status='pending').select_related('author', 'topic', 'topic__category').order_by('created_at')
    
    return render(request, 'forum/moderate_posts.html', {
        'pending_posts': pending_posts
    })


@login_required
def approve_post(request, post_id):
    """Одобрить пост и начислить вознаграждение"""
    if not request.user.is_staff:
        messages.error(request, 'Доступ запрещён.')
        return redirect('forum:forum')
    
    post = get_object_or_404(Post, id=post_id)
    
    if post.status != 'pending':
        messages.error(request, 'Этот пост уже обработан.')
        return redirect('forum:moderate_posts')
    
    # Одобряем пост
    post.status = 'approved'
    post.save()
    
    # Начисляем вознаграждение пользователю
    if post.reward_amount > 0:
        post.author.balance += post.reward_amount
        post.author.save()
        messages.success(request, f'Пост одобрен. Пользователю начислено {post.reward_amount}₽')
    else:
        messages.success(request, 'Пост одобрен.')

    # Установим флаг для автора, чтобы он увидел отметку в навигации
    try:
        if hasattr(post.author, 'has_unseen_approved_post'):
            post.author.has_unseen_approved_post = True
            post.author.save(update_fields=['has_unseen_approved_post'])
    except Exception:
        # Не критично — просто пропустим, логирование при необходимости покрыто отдельно
        pass
    
    return redirect('forum:moderate_posts')


@login_required
def reject_post(request, post_id):
    """Отклонить пост с причиной"""
    if not request.user.is_staff:
        messages.error(request, 'Доступ запрещён.')
        return redirect('forum:forum')
    
    post = get_object_or_404(Post, id=post_id)
    
    if post.status != 'pending':
        messages.error(request, 'Этот пост уже обработан.')
        return redirect('forum:moderate_posts')
    
    if request.method == 'POST':
        reason = request.POST.get('reason', 'Не соответствует правилам форума')
        
        # Отклоняем пост
        post.status = 'rejected'
        post.rejection_reason = reason
        post.save()
        
        messages.success(request, f'Пост отклонен. Пользователю отправлено уведомление.')
        return redirect('forum:moderate_posts')
    
    return render(request, 'forum/reject_post.html', {
        'post': post
    })

def search(request):
    """Поиск по форуму"""
    query = request.GET.get('q', '').strip()
    results = []
    
    if query:
        results = Topic.objects.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) |
            Q(posts__content__icontains=query)
        ).select_related('category', 'author').annotate(
            posts_count=Count('posts')
        ).distinct()
    
    return render(request, 'forum/search.html', {
        'query': query,
        'results': results
    })

@login_required
def toggle_topic(request, topic_id):
    """Закрытие/открытие темы (только для модераторов)"""
    topic = get_object_or_404(Topic, id=topic_id)
    if request.user.is_staff:
        topic.is_closed = not topic.is_closed
        topic.save()
        action = "закрыта" if topic.is_closed else "открыта"
        messages.success(request, f'Тема {action}!')
    else:
        messages.error(request, 'У вас нет прав для выполнения этого действия.')
    return redirect('forum:topic_posts', topic_id=topic.id)

@login_required
def toggle_pin(request, topic_id):
    """Закрепление/открепление темы (только для модераторов)"""
    topic = get_object_or_404(Topic, id=topic_id)
    if request.user.is_staff:
        topic.is_pinned = not topic.is_pinned
        topic.save()
        action = "закреплена" if topic.is_pinned else "откреплена"
        messages.success(request, f'Тема {action}!')
    else:
        messages.error(request, 'У вас нет прав для выполнения этого действия.')
    return redirect('forum:topic_posts', topic_id=topic.id)

@login_required
def edit_topic(request, topic_id):
    """Редактирование темы"""
    topic = get_object_or_404(Topic, id=topic_id)
    if request.user != topic.author and not request.user.is_staff:
        messages.error(request, 'У вас нет прав для редактирования этой темы.')
        return redirect('forum:topic_posts', topic_id=topic.id)
    
    if request.method == 'POST':
        form = TopicForm(request.POST, instance=topic)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тема успешно отредактирована!')
            return redirect('forum:topic_posts', topic_id=topic.id)
    else:
        form = TopicForm(instance=topic)
    
    return render(request, 'forum/edit_topic.html', {
        'form': form,
        'topic': topic
    })

@login_required
def delete_post(request, post_id):
    """Удаление сообщения (только для модераторов)"""
    post = get_object_or_404(Post, id=post_id)
    topic_id = post.topic.id
    
    # Разрешаем удалять посты модераторам (стандартное поведение)
    # и даём возможность автору удалить своё собственное сообщение
    # (полезно для отмены отправки на модерацию)
    logger = logging.getLogger('apps.forum')
    User = get_user_model()

    if request.user.is_staff:
        # Модератор может удалять любые сообщения
        post.delete()
        messages.success(request, 'Сообщение удалено!')
        logger.info(f"Moderator {request.user.username} deleted post {post_id} in topic {topic_id}")
    elif request.user == post.author:
        # Автор может удалить своё сообщение (включая ожидающие одобрения)
        pending = (post.status == 'pending')
        post_title = post.topic.title if post.topic else ''
        post.delete()
        messages.success(request, 'Ваше сообщение удалено!')
        logger.info(f"User {request.user.username} deleted own post {post_id} (pending={pending}) in topic {topic_id}")

        # Отправить уведомление модераторам, если пост был в ожидании
        if pending:
            try:
                moderators = User.objects.filter(is_staff=True).exclude(email='')
                if moderators.exists():
                    subject = f"Пользователь отменил пост #{post_id} в теме \"{post_title}\""
                    body = (
                        f"Пользователь {request.user.username} (id={request.user.id}) удалил своё сообщение #{post_id} "
                        f"в теме '{post_title}' вместо отправки на модерацию.\n\n"
                        f"Ссылка: {request.build_absolute_uri(request.path)}\n\n"
                        "Если необходимо, проверьте историю или свяжитесь с пользователем."
                    )
                    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@localhost'
                    recipient_list = [m.email for m in moderators]
                    send_mail(subject, body, from_email, recipient_list, fail_silently=True)
                    logger.debug(f"Sent moderator notification about deleted pending post {post_id} to {len(recipient_list)} moderators")
            except Exception as e:
                logger.exception(f"Failed to send moderator notification for deleted post {post_id}: {e}")
    else:
        messages.error(request, 'У вас нет прав для удаления этого сообщения.')
    
    return redirect('forum:topic_posts', topic_id=topic_id)

@login_required
def delete_topic(request, topic_id):
    """Удаление темы (только для модераторов)"""
    topic = get_object_or_404(Topic, id=topic_id)
    category_id = topic.category.id
    
    if request.user.is_staff:
        topic.delete()
        messages.success(request, 'Тема удалена!')
        return redirect('forum:category', category_id=category_id)
    else:
        messages.error(request, 'У вас нет прав для удаления тем.')
        return redirect('forum:topic_posts', topic_id=topic_id)

def user_topics(request, user_id):
    """Темы конкретного пользователя"""
    from django.contrib.auth.models import User
    user = get_object_or_404(User, id=user_id)
    
    topics_list = Topic.objects.filter(author=user).select_related('category').annotate(
        posts_count=Count('posts'),
        last_activity=Max('posts__created_at')
    ).order_by('-created_at')
    
    paginator = Paginator(topics_list, 15)
    page = request.GET.get('page')
    topics = paginator.get_page(page)
    
    return render(request, 'forum/user_topics.html', {
        'profile_user': user,
        'topics': topics
    })

def user_posts(request, user_id):
    """Сообщения конкретного пользователя"""
    from django.contrib.auth.models import User
    user = get_object_or_404(User, id=user_id)
    
    posts_list = Post.objects.filter(author=user).select_related('topic', 'topic__category').order_by('-created_at')
    
    paginator = Paginator(posts_list, 15)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    return render(request, 'forum/user_posts.html', {
        'profile_user': user,
        'posts': posts
    })

@login_required
def mark_all_read(request):
    """Пометить все темы как прочитанные"""
    # Сохраняем время последнего посещения в сессии
    request.session['forum_last_visit'] = str(timezone.now())
    messages.success(request, 'Все темы помечены как прочитанные!')
    return redirect('forum:forum')

def popular_topics(request):
    """Популярные темы (по просмотрам)"""
    topics_list = Topic.objects.select_related('category', 'author').annotate(
        posts_count=Count('posts'),
        last_activity=Max('posts__created_at')
    ).order_by('-views', '-created_at')
    
    paginator = Paginator(topics_list, 20)
    page = request.GET.get('page')
    topics = paginator.get_page(page)
    
    return render(request, 'forum/popular_topics.html', {
        'topics': topics,
        'title': 'Популярные темы'
    })

def active_topics(request):
    """Активные темы (по последней активности)"""
    topics_list = Topic.objects.select_related('category', 'author').annotate(
        posts_count=Count('posts'),
        last_activity=Max('posts__created_at')
    ).order_by('-last_activity', '-created_at')
    
    paginator = Paginator(topics_list, 20)
    page = request.GET.get('page')
    topics = paginator.get_page(page)
    
    return render(request, 'forum/popular_topics.html', {
        'topics': topics,
        'title': 'Активные темы'
    })

@login_required
def subscribe_topic(request, topic_id):
    """Подписка на тему"""
    topic = get_object_or_404(Topic, id=topic_id)
    # Здесь можно реализовать логику подписки
    messages.success(request, f'Вы подписались на тему "{topic.title}"')
    return redirect('forum:topic_posts', topic_id=topic.id)

@login_required
def unsubscribe_topic(request, topic_id):
    """Отписка от темы"""
    topic = get_object_or_404(Topic, id=topic_id)
    # Здесь можно реализовать логику отписки
    messages.success(request, f'Вы отписались от темы "{topic.title}"')
    return redirect('forum:topic_posts', topic_id=topic.id)

def statistics(request):
    """Статистика форума"""
    from django.db.models import Count, Max
    from django.contrib.auth.models import User
    
    total_topics = Topic.objects.count()
    total_posts = Post.objects.count()
    total_users = User.objects.count()
    latest_user = User.objects.order_by('-date_joined').first()
    
    # Самые активные пользователи
    active_users = User.objects.annotate(
        topics_count=Count('topics'),
        posts_count=Count('posts')
    ).order_by('-posts_count')[:10]
    
    # Самые популярные категории
    popular_categories = Category.objects.annotate(
        topics_count=Count('topics'),
        posts_count=Count('topics__posts')
    ).order_by('-posts_count')[:5]
    
    return render(request, 'forum/statistics.html', {
        'total_topics': total_topics,
        'total_posts': total_posts,
        'total_users': total_users,
        'latest_user': latest_user,
        'active_users': active_users,
        'popular_categories': popular_categories,
    })