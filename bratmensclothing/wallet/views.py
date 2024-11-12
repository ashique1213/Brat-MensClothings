from django.shortcuts import render,redirect
from .models import Wallet,Transaction
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.cache import never_cache


@never_cache
def view_wallet(request):
    if request.user.is_authenticated:
        user = request.user
        try:
            user_wallet = Wallet.objects.get(user_id=user.userid)  
        except Wallet.DoesNotExist:
            user_wallet = None

        if not user_wallet:
            return render(request, 'user/wallet.html', {'error': 'No wallet found for this user.'})

        user_transaction = Transaction.objects.filter(wallet_id=user_wallet)

        return render(request, 'user/wallet.html', 
                    {
                        'user_transaction': user_transaction,
                        'user_wallet': user_wallet
                        })
    
    return redirect('accounts:login_user')
