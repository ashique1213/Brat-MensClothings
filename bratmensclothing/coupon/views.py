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


def is_staff(user):
    return user.is_staff

@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff, 'accounts:admin_login')
def coupon_details(request):
    categories = Category.objects.filter(is_deleted=False)

    coupons = Coupon.objects.all()
    return render(request, 'admin/coupon.html', {'coupons': coupons,'categories':categories})

@never_cache
def add_coupon(request):
    categories = Category.objects.filter(is_deleted=False)

    if request.method == 'POST':
        code = request.POST.get('code')
        category = request.POST.get('category')
        discount_amount = request.POST.get('discount_amount')
        min_purchase_amount = request.POST.get('min_purchase_amount')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        usage_limit = request.POST.get('usage_limit')
        
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
            messages.success(request, "Coupon added successfully!")
        else:
            messages.error(request, "Failed to add coupon. Please ensure all fields are filled.")
        
        return redirect('coupon:coupon_details')
    
    return render(request, 'admin/coupon.html',{'categories':categories})

def edit_coupon(request, coupon_id):
    coupons = get_object_or_404(Coupon, coupon_id=coupon_id)

    if request.method == 'POST':
        code = request.POST.get('code')
        category = request.POST.get('category')
        discount_amount = request.POST.get('discount_amount')
        min_purchase_amount = request.POST.get('min_purchase_amount')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        usage_limit = request.POST.get('usage_limit')

        coupons.code = code
        coupons.discount_amount = discount_amount
        coupons.min_purchase_amount = min_purchase_amount
        coupons.valid_from = start_date
        coupons.valid_to = end_date
        coupons.usage_limit = usage_limit
        coupons.category = category

        coupons.save()

        return redirect('coupon:coupon_details')  

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
    

# @never_cache
# def apply_coupon(request):
#     if request.user.is_authenticated:
#         user = request.user
#         cart = get_object_or_404(Cart, user=user)
#         cart_items = CartItem.objects.filter(cart=cart)
        
#         if request.method == 'POST':    
#             code = request.POST.get('couponcode', '').strip()
#             print("Coupon code entered:", code)

#             try:
#                 coupon = Coupon.objects.get(code__iexact=code)

                
#                 if CouponUser.objects.filter(user=user, status=True).exists():
#                     messages.error(request, "You have already applied a coupon.")
                    
#                 else:
#                     coupon_category = coupon.category

#                     if coupon_category != 'None': 
#                         all_same_category = all(
#                             cart_item.variant.product.category == coupon_category
#                             for cart_item in cart_items
#                         )

#                         if not all_same_category:
#                             messages.error(request, "Coupon are not Available for all products")
#                             return redirect('cart:viewcart')
                    
#                     total = sum(item.item_total for item in cart_items)

#                     if total >= coupon.min_purchase_amount:
#                         CouponUser.objects.create(user=user, coupon=coupon, status=True)
#                         discount = min(total, coupon.discount_amount)
#                         messages.success(request, f"Coupon applied! You saved {discount}.")
#                     else:
#                         messages.info(request, f"The minimum purchase amount is not met for this coupon.")
            
#             except Coupon.DoesNotExist:
#                 messages.error(request, "Invalid coupon code. Please try again.")
        
#         return redirect('cart:viewcart')






@never_cache
def apply_coupon(request):
    if request.user.is_authenticated:
        user = request.user
        cart = get_object_or_404(Cart, user=user)
        cart_items = CartItem.objects.filter(cart=cart)

        if request.method == 'POST':
            code = request.POST.get('couponcode', '').strip()
            print("Coupon code entered:", code)

            try:
                coupon = Coupon.objects.get(code__iexact=code)

                # Check if the user has already applied this coupon
                # if CouponUser.objects.filter(user=user, coupon=coupon, status=True).exists():
                #     messages.error(request, "You have already applied this coupon.")
                if CouponUser.objects.filter(user=user, coupon=coupon, status=False).exists():
                    messages.error(request, "You have already applied this coupon.")
                else:
                    coupon_category = coupon.category

                    # Check if the coupon applies to the products' categories
                    if coupon_category != 'None':
                        all_same_category = all(
                            cart_item.variant.product.category == coupon_category
                            for cart_item in cart_items
                        )
                        if not all_same_category:
                            messages.error(request, "Coupon is not available for all products in the cart.")
                            return redirect('cart:viewcart')

                    total = sum(item.item_total for item in cart_items)
                    
                    if total >= coupon.min_purchase_amount:
                        # Create the CouponUser record to track the coupon application
                        CouponUser.objects.create(user=user, coupon=coupon, status=True)
                        discount = min(total, coupon.discount_amount)
                        messages.success(request, f"Coupon applied! You saved {discount}.")
                    else:
                        messages.info(request, f"The minimum purchase amount for this coupon is {coupon.min_purchase_amount}.")
            except Coupon.DoesNotExist:
                messages.error(request, "Invalid coupon code. Please try again.")

        return redirect('cart:viewcart')















@never_cache
def remove_coupon(request):
    if request.user.is_authenticated:
        user = request.user
        try:
            couponuser = CouponUser.objects.get(user=user)
            couponuser.delete()  
            messages.success(request, "Coupon removed successfully.")
        except CouponUser.DoesNotExist:
            messages.error(request, "No coupon applied to remove.")

    return redirect('cart:viewcart')