# apps/auction/forms.py
from django import forms
from .models import Auction, Bid, AuctionServer

class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ['title', 'description', 'starting_price', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            if end_time <= start_time:
                raise forms.ValidationError("Время окончания должно быть позже времени начала")
        
        return cleaned_data

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['bid_amount']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bid_amount'].widget.attrs.update({
            'placeholder': 'Введите сумму ставки',
            'min': '0.01',
            'step': '0.01'
        })

class AuctionServerForm(forms.ModelForm):
    class Meta:
        model = AuctionServer
        fields = ['name', 'description', 'mod', 'slots', 'plan', 'ip_address', 'port', 'starting_price', 'end_date']
        widgets = {
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['starting_price'].widget.attrs.update({
            'min': '0.01',
            'step': '0.01'
        })
        self.fields['slots'].widget.attrs.update({
            'min': '1'
        })
        self.fields['port'].widget.attrs.update({
            'min': '1',
            'max': '65535'
        })

class AuctionBidForm(forms.ModelForm):
    class Meta:
        model = Bid  # Используем существующую модель Bid
        fields = ['bid_amount']
    
    def __init__(self, *args, **kwargs):
        self.auction = kwargs.pop('auction', None)
        super().__init__(*args, **kwargs)
        self.fields['bid_amount'].widget.attrs.update({
            'placeholder': 'Введите сумму ставки',
            'min': '0.01',
            'step': '0.01',
            'class': 'form-control'
        })
    
    def clean_bid_amount(self):
        bid_amount = self.cleaned_data.get('bid_amount')
        
        if self.auction:
            # Проверяем что ставка выше текущей цены
            if bid_amount <= self.auction.current_price:
                raise forms.ValidationError(
                    f"Ставка должна быть выше текущей цены ({self.auction.current_price}₽)"
                )
            
            # Проверяем что ставка выше начальной цены (если нет других ставок)
            if self.auction.current_price == self.auction.starting_price and bid_amount <= self.auction.starting_price:
                raise forms.ValidationError(
                    f"Первая ставка должна быть выше начальной цены ({self.auction.starting_price}₽)"
                )
        
        return bid_amount