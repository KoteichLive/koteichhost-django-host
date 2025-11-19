# apps/auction/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.db.models import Q
from django.http import JsonResponse
from .models import Auction, Bid, AuctionServer, AuctionBid, AuctionHistory
from .forms import AuctionForm, BidForm

# ДОБАВЬТЕ ЭТУ ФУНКЦИЮ
def auction_view(request):
    """Основная страница аукциона"""
    active_auctions = AuctionServer.objects.filter(status='active')
    recent_bids = AuctionBid.objects.select_related('auction', 'bidder').order_by('-created_at')[:10]
    
    context = {
        'active_auctions': active_auctions,
        'recent_bids': recent_bids,
    }
    return render(request, 'auction/auction.html', context)

# ОСТАВЬТЕ СУЩЕСТВУЮЩИЕ ФУНКЦИИ
def auction_list(request):
    auctions = Auction.objects.filter(status='active')
    return render(request, 'auction/auction_list.html', {'auctions': auctions})

def auction_detail(request, auction_id):
    auction = get_object_or_404(AuctionServer, id=auction_id)
    bids = auction.bids.select_related('bidder').order_by('-created_at')
    
    context = {
        'auction': auction,
        'bids': bids,
    }
    return render(request, 'auction/auction_detail.html', context)

@login_required
def create_auction(request):
    if request.method == 'POST':
        form = AuctionForm(request.POST)
        if form.is_valid():
            auction = form.save(commit=False)
            auction.created_by = request.user
            auction.save()
            return redirect('auction:auction_detail', auction_id=auction.id)
    else:
        form = AuctionForm()
    return render(request, 'auction/create_auction.html', {'form': form})

@login_required
def place_bid(request, auction_id):
    auction = get_object_or_404(AuctionServer, id=auction_id)
    
    if request.method == 'POST':
        form = BidForm(request.POST)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.auction = auction
            bid.bidder = request.user
            bid.save()
            
            # Обновляем текущую цену
            auction.current_price = bid.bid_amount
            auction.save()
            
            # Создаем запись в истории
            AuctionHistory.objects.create(
                auction=auction,
                action='bid',
                user=request.user,
                description=f'Ставка: {bid.bid_amount}₽'
            )
            
            return redirect('auction:auction_detail', auction_id=auction.id)
    else:
        form = BidForm()
    
    context = {
        'form': form,
        'auction': auction
    }
    return render(request, 'auction/place_bid.html', context)

@login_required
def my_auctions(request):
    auctions = AuctionServer.objects.filter(owner=request.user)
    return render(request, 'auction/my_auctions.html', {'auctions': auctions})

@login_required
def my_bids(request):
    bids = AuctionBid.objects.filter(bidder=request.user).select_related('auction')
    return render(request, 'auction/my_bids.html', {'bids': bids})

@login_required
def cancel_auction(request, auction_id):
    auction = get_object_or_404(AuctionServer, id=auction_id, owner=request.user)
    
    if request.method == 'POST':
        auction.status = 'cancelled'
        auction.save()
        
        # Создаем запись в истории
        AuctionHistory.objects.create(
            auction=auction,
            action='cancelled',
            user=request.user,
            description='Аукцион отменен владельцем'
        )
        
        return redirect('auction:my_auctions')
    
    return render(request, 'auction/cancel_auction.html', {'auction': auction})

def get_auction_data(request):
    """API endpoint для получения данных аукциона"""
    auctions = AuctionServer.objects.filter(status='active').values(
        'id', 'name', 'current_price', 'end_date'
    )
    return JsonResponse(list(auctions), safe=False)