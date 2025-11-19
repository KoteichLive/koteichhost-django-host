# forum/urls.py
from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    path('', views.forum, name='forum'),
    path('category/<int:category_id>/', views.category, name='category'),
    path('topic/<int:topic_id>/', views.topic_posts, name='topic_posts'),
    path('topic/create/', views.create_topic, name='create_topic'),
    path('topic/<int:topic_id>/add_post/', views.add_post, name='add_post'),
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:post_id>/history/', views.post_history, name='post_history'),
    path('search/', views.search, name='search'),
    path('topic/<int:topic_id>/toggle/', views.toggle_topic, name='toggle_topic'),
    path('topic/<int:topic_id>/pin/', views.toggle_pin, name='toggle_pin'),
    path('topic/<int:topic_id>/edit/', views.edit_topic, name='edit_topic'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    # Модерация
    path('moderate/', views.moderate_posts, name='moderate_posts'),
    path('post/<int:post_id>/approve/', views.approve_post, name='approve_post'),
    path('post/<int:post_id>/reject/', views.reject_post, name='reject_post'),
]