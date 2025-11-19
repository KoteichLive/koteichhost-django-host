# apps/dashboard/urls.py
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/servers/', views.get_servers_data, name='api_servers'),
    path('api/servers/<int:server_id>/extend/', views.extend_server, name='extend_server'),
    path('api/servers/<int:server_id>/auction/', views.put_on_auction, name='put_on_auction'),
]