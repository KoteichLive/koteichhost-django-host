from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'  # Убедитесь что это есть

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
]
