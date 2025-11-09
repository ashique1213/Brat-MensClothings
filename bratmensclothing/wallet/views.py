from django.shortcuts import render, redirect
from .models import Wallet, Transaction
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import logging
logger = logging.getLogger('wallet.views')


@never_cache
def view_wallet(request):
    logger.debug("view_wallet called | user=%s | authenticated=%s", request.user, request.user.is_authenticated)

    if not request.user.is_authenticated:
        logger.info("Unauthenticated access to wallet | redirecting to login")
        return redirect('accounts:login_user')

    user = request.user

    try:
        user_wallet = Wallet.objects.get(user_id=user.userid)
        logger.debug("Wallet found | user_id=%s | wallet_id=%s | balance=%s", user.userid, user_wallet.wallet_id, user_wallet.balance)
    except Wallet.DoesNotExist:
        user_wallet = None
        logger.warning("Wallet not found for user | user_id=%s", user.userid)

    if not user_wallet:
        logger.info("Wallet view rendered with error | user_id=%s", user.userid)
        return render(request, 'user/wallet.html', {'error': 'No wallet found for this user.'})

    user_transaction = Transaction.objects.filter(wallet_id=user_wallet).order_by('-created_at')
    logger.debug("Transactions loaded | wallet_id=%s | count=%d", user_wallet.wallet_id, user_transaction.count())

    # Pagination
    paginator = Paginator(user_transaction, 2)
    page_number = request.GET.get('page')

    try:
        page_obj = paginator.get_page(page_number)
        logger.debug("Page loaded | page=%s | has_next=%s | has_previous=%s", page_obj.number, page_obj.has_next(), page_obj.has_previous())
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
        logger.debug("Invalid page number | defaulting to page 1")
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
        logger.debug("Page out of range | defaulting to last page")

    logger.info("Wallet page rendered successfully | user_id=%s | transactions_count=%d | current_page=%s", 
                user.userid, user_transaction.count(), page_obj.number)

    return render(request, 'user/wallet.html', {
        'user_transaction': page_obj,
        'user_wallet': user_wallet,
        'page_obj': page_obj
    })