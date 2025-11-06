from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import Users
from products.models import ProductDetails, Category, Brand, VariantSize
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from .models import Wishlist
import logging
logger = logging.getLogger('wishlist.views')


@never_cache
def view_wishlist(request):
    logger.debug("view_wishlist called | user=%s | authenticated=%s", request.user, request.user.is_authenticated)

    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product__product')
        logger.info("Wishlist loaded | user_id=%s | items_count=%d", request.user.userid, wishlist_items.count())
    else:
        wishlist_items = []
        logger.info("Guest accessed wishlist | items_count=0")

    return render(request, 'user/wishlist.html', {'Wishlist_items': wishlist_items})


@never_cache
def add_to_wishlist(request, product_id):
    logger.debug("add_to_wishlist called | product_id=%s | user=%s", product_id, request.user)

    if not request.user.is_authenticated:
        logger.info("Unauthenticated add to wishlist | product_id=%s", product_id)
        messages.error(request, "You need to be logged in.")
        return redirect('accounts:login_user')

    try:
        variants = VariantSize.objects.filter(product__product_id=product_id)
        if not variants.exists():
            logger.warning("No variants found for product | product_id=%s", product_id)
            messages.error(request, "This product is not available.")
            return redirect('userss:category_details')

        variant = variants.first()
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=variant)

        if created:
            logger.info("Item added to wishlist | user_id=%s | variant_id=%s", request.user.userid, variant.variant_id)
            messages.success(request, "Item added to your wishlist!")
        else:
            logger.info("Item already in wishlist | user_id=%s | variant_id=%s", request.user.userid, variant.variant_id)
            messages.info(request, "Item already in your wishlist.")

    except Exception as e:
        logger.error("Error adding to wishlist | product_id=%s | error=%s", product_id, e, exc_info=True)
        messages.error(request, "Failed to add item to wishlist.")

    return redirect('userss:category_details')


@never_cache
def remove_wishlist(request, variant_id):
    logger.debug("remove_wishlist called | variant_id=%s | user=%s", variant_id, request.user)

    try:
        wishlist_item = Wishlist.objects.filter(product_id=variant_id, user=request.user)
        if wishlist_item.exists():
            wishlist_item.delete()
            logger.info("Item removed from wishlist | variant_id=%s | user_id=%s", variant_id, request.user.userid)
            messages.success(request, "Item removed from your wishlist!")
        else:
            logger.warning("Wishlist item not found | variant_id=%s | user_id=%s", variant_id, request.user.userid)
            messages.info(request, "Item not found in your wishlist.")
    except Exception as e:
        logger.error("Error removing from wishlist | variant_id=%s | error=%s", variant_id, e, exc_info=True)
        messages.error(request, "Failed to remove item.")

    return redirect('wishlist:viewwishlist')


@never_cache
def clear_wishlist(request):
    logger.debug("clear_wishlist called | user=%s", request.user)

    if not request.user.is_authenticated:
        logger.info("Unauthenticated clear wishlist attempt")
        messages.error(request, "You need to be logged in.")
        return redirect('wishlist:viewwishlist')

    try:
        deleted_count, _ = Wishlist.objects.filter(user=request.user).delete()
        logger.info("Wishlist cleared | user_id=%s | items_deleted=%d", request.user.userid, deleted_count)
        messages.success(request, "Your wishlist has been cleared!")
    except Exception as e:
        logger.error("Error clearing wishlist | user_id=%s | error=%s", request.user.userid, e, exc_info=True)
        messages.error(request, "Failed to clear wishlist.")

    return redirect('wishlist:viewwishlist')