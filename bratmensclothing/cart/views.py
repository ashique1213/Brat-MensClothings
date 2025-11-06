from django.shortcuts import render,redirect,get_object_or_404
from accounts.models import Users
from products.models import ProductDetails,Category,Brand,VariantSize
from users.models import Address
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import never_cache
from django.db.models import Q
import re
from .models import Cart, CartItem
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import CartItem
from coupon.models import Coupon,CouponUser
from decimal import Decimal
from offer.models import Product_Offers,Brand_Offers
from django.utils import timezone
from django.contrib.messages import get_messages
import logging
logger = logging.getLogger('cart.views')


@never_cache
def view_cart(request):
    logger.debug("view_cart called | method=%s | user=%s", request.method, request.user)

    cart_items = []
    grand_total = Decimal('0.0')
    tax = Decimal('0.0')
    delivery_charge = Decimal('50.0')
    coupon_discount = Decimal('0.0')
    couponuser = None
    total = Decimal('0.0')
    coupons = []

    if request.user.is_authenticated:
        user = request.user
        cart = Cart.objects.filter(user=user).first()
        if cart:
            cart_items = CartItem.objects.filter(cart=cart).order_by('cartitem_id')

            for cart_item in cart_items:
                variant = cart_item.variant
                product = variant.product

                product_offer = Product_Offers.objects.filter(
                    product_id=product,
                    status=True,
                    started_date__lte=timezone.now(),
                    end_date__gte=timezone.now()
                ).first()

                brand_offer = Brand_Offers.objects.filter(
                    brand_id=product.brand,
                    status=True,
                    started_date__lte=timezone.now(),
                    end_date__gte=timezone.now()
                ).first()

                discounted_price = product.price

                if product_offer:
                    discounted_price = product.price - product_offer.offer_price

                if brand_offer:
                    brand_discounted_price = product.price - brand_offer.offer_price
                    discounted_price = min(discounted_price, brand_discounted_price)

                cart_item.variant.product.price = discounted_price

            try:
                couponuser = CouponUser.objects.get(user=user, status=True)
                coupon_discount = couponuser.coupon.discount_amount
                logger.info("Active coupon applied for user %s: %s", user.username, couponuser.coupon.code)
            except CouponUser.DoesNotExist:
                couponuser = None

            total = sum(item.item_total for item in cart_items)

            if couponuser:
                coupon = couponuser.coupon
                if total < coupon.min_purchase_amount:
                    couponuser.delete()
                    coupon_discount = Decimal('0.0')
                    messages.info(request, "Coupon removed! Total is less than the minimum purchase amount.")
                    logger.info("Coupon removed for user %s: total %s < min %s", user.username, total, coupon.min_purchase_amount)

            if total >= (coupon.min_purchase_amount if couponuser else 0):
                discount = min(total, coupon_discount)
                total_after_discount = total - discount
            else:
                total_after_discount = total

            tax_rate = Decimal('0.02')
            tax = total_after_discount * tax_rate
            grand_total = total_after_discount + tax + delivery_charge

            used_coupon_ids = CouponUser.objects.filter(user=user).values_list('coupon_id', flat=True)
            coupons = Coupon.objects.filter(
                ~Q(coupon_id__in=used_coupon_ids),
                is_active=False,
                usage_limit__gt=0,
                valid_from__lte=timezone.now().date(),
                valid_to__gte=timezone.now().date()
            )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            storage = get_messages(request)
            message_list = [{'message': message.message, 'level': message.level_tag} for message in storage]

            logger.debug("AJAX cart view response | items=%d | grand_total=%s", len(cart_items), grand_total)

            return JsonResponse({
                'success': True,
                'subtotal': float(total),
                'tax': float(tax),
                'discount': float(coupon_discount),
                'grand_total': float(grand_total),
                'cart_items': [
                    {
                        'cartitem_id': item.cartitem_id,
                        'quantity': item.quantity,
                        'item_total': float(item.item_total)
                    } for item in cart_items
                ],
                'couponuser': {
                    'id': couponuser.id if couponuser else None,
                    'code': couponuser.coupon.code if couponuser else None,
                    'status': couponuser.status if couponuser else False
                },
                'coupons': [
                    {
                        'code': coupon.code,
                        'discount_amount': float(coupon.discount_amount),
                        'min_purchase_amount': float(coupon.min_purchase_amount),
                        'category': coupon.category
                    } for coupon in coupons
                ],
                'messages': message_list
            })

        logger.info("Cart page rendered for user %s | items=%d | total=%s", user.username, len(cart_items), grand_total)
        return render(request, 'user/cart.html', {
            'cart_items': cart_items,
            'grand_total': grand_total,
            'tax': tax,
            'cart': cart,
            'delivery_charge': delivery_charge,
            'coupons': coupons,
            'couponuser': couponuser,
            'discount': coupon_discount,
            'total': total
        })

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        logger.warning("AJAX cart request without authentication")
        return JsonResponse({
            'success': False,
            'message': 'User not authenticated or no cart items.',
            'messages': []
        })

    logger.debug("Guest cart page rendered (no auth)")
    return render(request, 'user/cart.html')


@never_cache
def add_to_cart(request, variant_id):
    logger.debug("add_to_cart called | variant_id=%s | method=%s", variant_id, request.method)

    if request.user.is_authenticated:
        variant = get_object_or_404(VariantSize, variant_id=variant_id)
        quantity = int(request.POST.get('quantity', 1))

        if variant.qty == 0:
            messages.error(request, "The product is out of stock")
            logger.warning("Add to cart failed: variant %s out of stock", variant_id)
            return redirect('userss:product_details', product_id=variant.product.product_id)
        
        if quantity > variant.qty:
            messages.error(request, "You have selected a quantity above the available stock.")
            logger.warning("Add to cart failed: requested %d > stock %d for variant %s", quantity, variant.qty, variant_id)
            return redirect('userss:product_details', product_id=variant.product.product_id)

        cart, created = Cart.objects.get_or_create(user=request.user)
        if created:
            logger.info("New cart created for user %s", request.user.username)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, variant=variant)
        
        if cart_item.quantity + quantity > 6:
            cart_item.quantity = 6  
            cart_item.save()
            messages.error(request, "You already have 6 in your cart")
            logger.info("Cart item capped at 6 for variant %s | user %s", variant_id, request.user.username)
            return redirect('userss:product_details', product_id=variant.product.product_id)
        else:
            cart_item.quantity += quantity
            cart_item.save()
            logger.info("Added %d of variant %s to cart | user %s | new qty=%d", quantity, variant_id, request.user.username, cart_item.quantity)

        messages.success(request, "Item added to cart successfully")
    else:
        messages.error(request, "Please log in to add items to your cart.")
        logger.warning("Add to cart attempted without login")

    return redirect('cart:viewcart')


def delete_item(request, cartitem_id):
    logger.debug("delete_item called | cartitem_id=%s | user=%s", cartitem_id, request.user)

    item = get_object_or_404(CartItem, cartitem_id=cartitem_id)

    if item.cart.user != request.user:
        logger.warning("Security: User %s tried to delete cart item %s belonging to another user", request.user, cartitem_id)
        messages.error(request, "You cannot delete this item.")
        return redirect('cart:viewcart')

    item.delete()
    logger.info("Cart item %s deleted by user %s", cartitem_id, request.user.username)
    messages.success(request, "Item deleted successfully ")
    return redirect('cart:viewcart')


@require_POST
def update_cart_item(request, cart_item_id):
    logger.debug("update_cart_item called | cart_item_id=%s | body=%s", cart_item_id, request.body)

    data = json.loads(request.body)
    quantity = int(data.get('quantity', 0))

    try:
        cart_item = CartItem.objects.get(cartitem_id=cart_item_id)
        variant = cart_item.variant

        if cart_item.cart.user != request.user:
            logger.warning("Security: User %s tried to update cart item %s of another user", request.user, cart_item_id)
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

        if quantity > variant.qty:
            logger.warning("Update failed: quantity %d > stock %d for variant %s", quantity, variant.qty, variant.variant_id)
            return JsonResponse({
                'success': False,
                'error': f"Quantity exceeds available stock. Only {variant.qty} left."
            }, status=400)

        old_qty = cart_item.quantity
        cart_item.quantity = quantity
        cart_item.save()

        logger.info("Cart item %s quantity updated: %d to %d | user %s", cart_item_id, old_qty, quantity, request.user.username)

        return JsonResponse({
            'success': True,
            'new_total': float(cart_item.item_total)
        })
    except CartItem.DoesNotExist:
        logger.error("Cart item %s not found during update", cart_item_id)
        return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)