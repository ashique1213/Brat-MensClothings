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



def is_staff(user):
    return user.is_staff

@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff, 'accounts:admin_login')
def coupon_details(request):
    categories = Category.objects.filter(is_deleted=False)

    search_query=request.GET.get('search','') 

    if search_query:
        coupons = Coupon.objects.filter(
           Q(code__icontains=search_query) | Q (category__icontains=search_query)
        ).order_by('-created_at')
    else:
        coupons = Coupon.objects.all()
    return render(request, 'admin/coupon.html', {'coupons': coupons,'categories':categories,'search_query':search_query})

@never_cache
def add_coupon(request):
    categories = Category.objects.filter(is_deleted=False)

    if request.method == 'POST':
        code = request.POST.get('code').strip()
        category = request.POST.get('category')
        discount_amount = request.POST.get('discount_amount').strip()
        min_purchase_amount = request.POST.get('min_purchase_amount')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        usage_limit = request.POST.get('usage_limit')

        errors={}
        if not code:
            errors['code_error']='Coupon Code required'
        elif len(code)<4:
            errors['code_error']='Coupon code contain atleast 4 charecter'
        elif Coupon.objects.filter(code__iexact=code).exists():
            errors['code_error']='Coupon code already exits'
        
        try:
            discount_amount = Decimal (discount_amount) 
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
            return JsonResponse({'success': False, 'errors': errors})
        

        if code and discount_amount and min_purchase_amount and start_date and end_date and usage_limit:
            Coupon.objects.create(
                code=code,
                category=category,
                discount_amount=discount_amount,
                min_purchase_amount=min_purchase_amount,
                valid_from=start_date,
                valid_to=end_date,
                usage_limit=usage_limit
            )
        return JsonResponse({'success': True, 'message': 'Brand added successfully!'})
        # return redirect('coupon:coupon_details')
    
    return render(request, 'admin/coupon.html',{'categories':categories})

def edit_coupon(request, coupon_id):
    coupons = get_object_or_404(Coupon, coupon_id=coupon_id)

    if request.method == 'POST':
        code = request.POST.get('code')
        category = request.POST.get('category').strip()
        discount_amount = request.POST.get('discount_amount').strip()
        min_purchase_amount = request.POST.get('min_purchase_amount')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        usage_limit = request.POST.get('usage_limit')

        errors={}
        if not code:
            errors['code_error']='Coupon Code required'
        elif len(code)<4:
            errors['code_error']='Coupon code contain atleast 4 charecter'
        elif Coupon.objects.filter(code__iexact=code).exclude(coupon_id=coupons.coupon_id).exists():
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
            return JsonResponse({'success': False, 'errors': errors})

        coupons.code = code
        coupons.discount_amount = discount_amount
        coupons.min_purchase_amount = min_purchase_amount
        coupons.valid_from = start_date
        coupons.valid_to = end_date
        coupons.usage_limit = usage_limit
        coupons.category = category

        coupons.save()
        return JsonResponse({'success': True, 'message': 'Coupon Updated successfully!'})
        # return redirect('coupon:coupon_details')  

    return render(request, 'admin/edit_coupon.html', {'coupons': coupons})


def soft_delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, coupon_id=coupon_id)
    coupon.is_active = True
    coupon.save()
    return redirect('coupon:coupon_details')

def restore_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, coupon_id=coupon_id)
    coupon.is_active = False
    coupon.save()
    return redirect('coupon:coupon_details')

def delete_coupon(request,coupon_id):
    code=Coupon.objects.get(coupon_id=coupon_id)
    code.delete()
    return redirect('coupon:coupon_details')
    

@never_cache
def apply_coupon(request):
    if request.user.is_authenticated:
        user = request.user
        cart = get_object_or_404(Cart, user=user)
        cart_items = CartItem.objects.filter(cart=cart)

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

                if CouponUser.objects.filter(user=user, coupon=coupon, status=False).exists():
                    return JsonResponse({'success': False, 'message': 'You have already applied this coupon.'})
                else:
                    coupon_category = coupon.category

                    # Check if the coupon applicable to all products
                    if coupon_category != 'None':
                        all_same_category = all(
                            # cart_item.variant.product.category == coupon_category
                            cart_item.variant.product.category.filter(category=coupon_category).exists()
                            for cart_item in cart_items
                        )
                        if not all_same_category:
                            return JsonResponse({'success': False, 'message': 'Coupon is not available for all products in the cart.'})

                    total = sum(item.item_total for item in cart_items)

                    if total >= coupon.min_purchase_amount:
                        # Create the CouponUser 
                        CouponUser.objects.create(user=user, coupon=coupon, status=True)
                        discount = min(total, coupon.discount_amount)
                        return JsonResponse({'success': True, 'message': f'Coupon applied! You saved {discount}.'})
                    else:
                        return JsonResponse({'success': False, 'message': f'The minimum purchase amount for this coupon is {coupon.min_purchase_amount}.'})

            except Coupon.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid coupon code. Please try again.'})

        return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@never_cache
def remove_coupon(request, id):
    if request.user.is_authenticated:
        user = request.user

        try:
            couponuser = CouponUser.objects.get(id=id, user=user)
            couponuser.delete()
            return JsonResponse({'success': True, 'message': 'Coupon removed successfully.'})
        except CouponUser.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Coupon not found.'})

    return JsonResponse({'success': False, 'message': 'User not authenticated.'})