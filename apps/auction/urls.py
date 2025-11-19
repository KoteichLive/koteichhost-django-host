# apps/auction/urls.py
from django.urls import path
from . import views

app_name = 'auction'

urlpatterns = [
    # ИЗМЕНИТЕ ЭТУ СТРОКУ:
    path('', views.auction_list, name='auction'),  # используем auction_list вместо auction_view
    
    path('create/', views.create_auction, name='create_auction'),
    path('<int:auction_id>/', views.auction_detail, name='auction_detail'),
    path('<int:auction_id>/bid/', views.place_bid, name='place_bid'),
    path('<int:auction_id>/cancel/', views.cancel_auction, name='cancel_auction'),
    path('my/auctions/', views.my_auctions, name='my_auctions'),
    path('my/bids/', views.my_bids, name='my_bids'),
    path('api/items/', views.get_auction_data, name='api_auction'),
]