from django.shortcuts import render,redirect
from .models import Wallet,Transaction
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


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

        user_transaction = Transaction.objects.filter(wallet_id=user_wallet).order_by('-created_at')


        # new
        paginator = Paginator(user_transaction, 2)  

        page_number = request.GET.get('page')

        try:
            page_obj = paginator.get_page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.get_page(1)
        except EmptyPage:
            page_obj = paginator.get_page(paginator.num_pages)

        return render(request, 'user/wallet.html', 
                    {
                       'user_transaction': page_obj,  
                    #    'user_transaction': user_transaction,  
                        'user_wallet': user_wallet,
                        'page_obj': page_obj
                        })
    
    return redirect('accounts:login_user')
