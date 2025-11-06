from django.shortcuts import render,redirect,get_object_or_404
from accounts.models import Users
from users.models import Address
from cart.models import Cart,CartItem
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import never_cache,cache_control
from django.http import JsonResponse
from decimal import Decimal
from django.core.paginator import Paginator
from .models import Coupon,CouponUser
from products.models import Category
from offer.models import Product_Offers,Brand_Offers
from django.utils import timezone
from django.db.models import Q
import logging
logger = logging.getLogger('coupon.views')


def is_staff(user):
    return user.is_staff

@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff, 'accounts:admin_login')
def coupon_details(request):
    logger.debug("coupon_details called | method=%s | user=%s", request.method, request.user)

    categories = Category.objects.filter(is_deleted=False)
    search_query = request.GET.get('search', '')

    if search_query:
        coupons = Coupon.objects.filter(
           Q(code__icontains=search_query) | Q(category__icontains=search_query)
        ).order_by('-created_at')
        logger.info("Coupon search performed: '%s' | results=%d", search_query, coupons.count())
    else:
        coupons = Coupon.objects.all()
        logger.debug("All coupons loaded | count=%d", coupons.count())

    return render(request, 'admin/coupon.html', {
        'coupons': coupons,
        'categories': categories,
        'search_query': search_query
    })


@never_cache
def add_coupon(request):
    logger.debug("add_coupon called | method=%s | user=%s", request.method, request.user)

    categories = Category.objects.filter(is_deleted=False)

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        category = request.POST.get('category')
        discount_amount = request.POST.get('discount_amount', '').strip()
        min_purchase_amount = request.POST.get('min_purchase_amount')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        usage_limit = request.POST.get('usage_limit')

        errors = {}

        if not code:
            errors['code_error'] = 'Coupon Code required'
        elif len(code) < 4:
            errors['code_error'] = 'Coupon code contain atleast 4 charecter'
        elif Coupon.objects.filter(code__iexact=code).exists():
            errors['code_error'] = 'Coupon code already exits'

        try:
            discount_amount = Decimal(discount_amount)
            if discount_amount >= 200:
                errors['discount_error'] = 'Discount amount must be less than 200'
        except ValueError:
            errors['discount_error'] = 'Discount amount must be a valid number'

        if not min_purchase_amount:
            errors['min_purchase_error'] = 'Min purchase amount is required.'
        else:
            try:
                min_purchase_amount = float(min_purchase_amount)
                if min_purchase_amount < 500:
                    errors['min_purchase_error'] = 'Min purchase amount must be at least 500.'
            except ValueError:
                errors['min_purchase_error'] = 'Invalid min purchase amount format. It must be a valid number.'

        if not usage_limit:
            errors['usage_limit_error'] = 'Usage limit is required.'
        else:
            try:
                usage_limit = int(usage_limit)
                if usage_limit < 1:
                    errors['usage_limit_error'] = 'Usage limit must be at least 1.'
            except ValueError:
                errors['usage_limit_error'] = 'Invalid usage limit format. It must be a valid integer.'

        if errors:
            logger.warning("Coupon creation failed | code=%s | errors=%s", code, errors)
            return JsonResponse({'success': False, 'errors': errors})

        try:
            Coupon.objects.create(
                code=code,
                category=category,
                discount_amount=discount_amount,
                min_purchase_amount=min_purchase_amount,
                valid_from=start_date,
                valid_to=end_date,
                usage_limit=usage_limit
            )
            logger.info("Coupon created successfully | code=%s | discount=%s | min=%s", code, discount_amount, min_purchase_amount)
            return JsonResponse({'success': True, 'message': 'Brand added successfully!'})
        except Exception as e:
            logger.error("Unexpected error creating coupon | code=%s | error=%s", code, e, exc_info=True)
            return JsonResponse({'success': False, 'errors': {'server': 'Failed to create coupon.'}})

    return render(request, 'admin/coupon.html', {'categories': categories})


def edit_coupon(request, coupon_id):
    logger.debug("edit_coupon called | coupon_id=%s | method=%s", coupon_id, request.method)

    coupon = get_object_or_404(Coupon, coupon_id=coupon_id)

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        category = request.POST.get('category', '').strip()
        discount_amount = request.POST.get('discount_amount', '').strip()
        min_purchase_amount = request.POST.get('min_purchase_amount')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        usage_limit = request.POST.get('usage_limit')

        errors = {}

        if not code:
            errors['code_error'] = 'Coupon Code required'
        elif len(code) < 4:
            errors['code_error'] = 'Coupon code contain atleast 4 charecter'
        elif Coupon.objects.filter(code__iexact=code).exclude(coupon_id=coupon.coupon_id).exists():
            errors['code_error'] = 'Coupon code already exists'

        try:
            discount_amount = Decimal(discount_amount)
            if discount_amount >= 200:
                errors['discount_error'] = 'Discount amount must be less than 200'
        except ValueError:
            errors['discount_error'] = 'Discount amount must be a valid number'

        if not min_purchase_amount:
            errors['min_purchase_error'] = 'Min purchase amount is required.'
        else:
            try:
                min_purchase_amount = float(min_purchase_amount)
                if min_purchase_amount < 500:
                    errors['min_purchase_error'] = 'Min purchase amount must be at least 500.'
            except ValueError:
                errors['min_purchase_error'] = 'Invalid min purchase amount format. It must be a valid number.'

        if not usage_limit:
            errors['usage_limit_error'] = 'Usage limit is required.'
        else:
            try:
                usage_limit = int(usage_limit)
                if usage_limit < 1:
                    errors['usage_limit_error'] = 'Usage limit must be at least 1.'
            except ValueError:
                errors['usage_limit_error'] = 'Invalid usage limit format. It must be a valid integer.'

        if errors:
            logger.warning("Coupon edit validation failed | coupon_id=%s | errors=%s", coupon_id, errors)
            return JsonResponse({'success': False, 'errors': errors})

        try:
            coupon.code = code
            coupon.discount_amount = discount_amount
            coupon.min_purchase_amount = min_purchase_amount
            coupon.valid_from = start_date
            coupon.valid_to = end_date
            coupon.usage_limit = usage_limit
            coupon.category = category
            coupon.save()
            logger.info("Coupon updated | coupon_id=%s | code=%s", coupon_id, code)
            return JsonResponse({'success': True, 'message': 'Coupon Updated successfully!'})
        except Exception as e:
            logger.error("Failed to update coupon | coupon_id=%s | error=%s", coupon_id, e, exc_info=True)
            return JsonResponse({'success': False, 'errors': {'server': 'Update failed.'}})

    return render(request, 'admin/edit_coupon.html', {'coupons': coupon})


def soft_delete_coupon(request, coupon_id):
    logger.debug("soft_delete_coupon called | coupon_id=%s", coupon_id)
    coupon = get_object_or_404(Coupon, coupon_id=coupon_id)
    coupon.is_active = True
    coupon.save()
    logger.info("Coupon soft-deleted (deactivated) | coupon_id=%s | code=%s", coupon_id, coupon.code)
    return redirect('coupon:coupon_details')


def restore_coupon(request, coupon_id):
    logger.debug("restore_coupon called | coupon_id=%s", coupon_id)
    coupon = get_object_or_404(Coupon, coupon_id=coupon_id)
    coupon.is_active = False
    coupon.save()
    logger.info("Coupon restored (activated) | coupon_id=%s | code=%s", coupon_id, coupon.code)
    return redirect('coupon:coupon_details')


def delete_coupon(request, coupon_id):
    logger.debug("delete_coupon called | coupon_id=%s", coupon_id)
    coupon = Coupon.objects.get(coupon_id=coupon_id)
    code = coupon.code
    coupon.delete()
    logger.info("Coupon permanently deleted | coupon_id=%s | code=%s", coupon_id, code)
    return redirect('coupon:coupon_details')


@never_cache
def apply_coupon(request):
    logger.debug("apply_coupon called | method=%s | user=%s", request.method, request.user)

    if not request.user.is_authenticated:
        logger.warning("apply_coupon called without authentication")
        return JsonResponse({'success': False, 'message': 'User not authenticated.'})

    user = request.user
    cart = get_object_or_404(Cart, user=user)
    cart_items = CartItem.objects.filter(cart=cart)

    # Apply offers to cart items
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

    if request.method == 'POST':
        code = request.POST.get('couponcode', '').strip()

        try:
            coupon = Coupon.objects.get(code__iexact=code)
            logger.debug("Coupon found: %s", code)

            if CouponUser.objects.filter(user=user, coupon=coupon, status=False).exists():
                logger.info("Coupon already used | user=%s | code=%s", user.username, code)
                return JsonResponse({'success': False, 'message': 'You have already applied this coupon.'})

            coupon_category = coupon.category

            # Category check
            if coupon_category != 'None':
                all_same_category = all(
                    cart_item.variant.product.category.filter(category=coupon_category).exists()
                    for cart_item in cart_items
                )
                if not all_same_category:
                    logger.info("Coupon category mismatch | code=%s | required=%s", code, coupon_category)
                    return JsonResponse({'success': False, 'message': 'Coupon is not available for all products in the cart.'})

            total = sum(item.item_total for item in cart_items)

            if total >= coupon.min_purchase_amount:
                CouponUser.objects.create(user=user, coupon=coupon, status=True)
                discount = min(total, coupon.discount_amount)
                logger.info("Coupon applied | user=%s | code=%s | discount=%s", user.username, code, discount)
                return JsonResponse({'success': True, 'message': f'Coupon applied! You saved {discount}.'})
            else:
                logger.info("Coupon min amount not met | total=%s | required=%s", total, coupon.min_purchase_amount)
                return JsonResponse({'success': False, 'message': f'The minimum purchase amount for this coupon is {coupon.min_purchase_amount}.'})

        except Coupon.DoesNotExist:
            logger.warning("Invalid coupon code attempted | code=%s | user=%s", code, user.username)
            return JsonResponse({'success': False, 'message': 'Invalid coupon code. Please try again.'})

    logger.warning("apply_coupon called with invalid method")
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@never_cache
def remove_coupon(request, id):
    logger.debug("remove_coupon called | id=%s | user=%s", id, request.user)

    if not request.user.is_authenticated:
        logger.warning("remove_coupon called without authentication")
        return JsonResponse({'success': False, 'message': 'User not authenticated.'})

    try:
        couponuser = CouponUser.objects.get(id=id, user=request.user)
        code = couponuser.coupon.code
        couponuser.delete()
        logger.info("Coupon removed | user=%s | code=%s", request.user.username, code)
        return JsonResponse({'success': True, 'message': 'Coupon removed successfully.'})
    except CouponUser.DoesNotExist:
        logger.warning("CouponUser not found for removal | id=%s | user=%s", id, request.user.username)
        return JsonResponse({'success': False, 'message': 'Coupon not found.'})