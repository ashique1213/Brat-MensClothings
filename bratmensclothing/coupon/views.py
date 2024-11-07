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


def is_staff(user):
    return user.is_staff

@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff, 'accounts:admin_login')
def coupon_details(request):
    coupons = Coupon.objects.all()
    return render(request, 'admin/coupon.html', {'coupons': coupons})

@never_cache
def add_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        discount_amount = request.POST.get('discount_amount')
        min_purchase_amount = request.POST.get('min_purchase_amount')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        usage_limit = request.POST.get('usage_limit')
        
        if code and discount_amount and min_purchase_amount and start_date and end_date and usage_limit:
            Coupon.objects.create(
                code=code,
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
    
    return render(request, 'admin/coupon.html')


def delete_coupon(request,coupon_id):
    code=Coupon.objects.get(coupon_id=coupon_id)
    code.delete()
    return redirect('coupon:coupon_details')
    

# @cache_control(private=True, no_cache=True)
# def apply_coupon(request):
#     if request.user.is_authenticated:
#         grand_total = Decimal('0.0')
#         tax = Decimal('0.0')
#         delivery_charge = Decimal('50.0')
        
#         user = request.user
#         cart = get_object_or_404(Cart, user=user)
#         cart_items = CartItem.objects.filter(cart=cart)
        
#         if request.method == 'POST':    
#             code = request.POST.get('couponcode', '').strip()
#             print("Coupon code entered:", code)

#             try:
#                 coupon = Coupon.objects.get(code__iexact=code)
                
#                 total = sum(items.item_total for items in cart_items)
#                 discount = min(total, coupon.discount_amount) 
#                 new_total = total - discount
                
#                 tax_rate = Decimal('0.02')
#                 tax = new_total * tax_rate
#                 grand_total = new_total + tax + delivery_charge
                
#                 messages.success(request, f"Coupon applied! You saved {discount}.")

#             except Coupon.DoesNotExist:
#                 messages.error(request, "Invalid coupon code. Please try again.")
        
#         coupons = Coupon.objects.all()
#         return redirect('cart:viewcart', {
#             'user': user,
#             'cart_items': cart_items,
#             'tax': tax,
#             'delivery_charge': delivery_charge,
#             'grand_total': grand_total,
#             'coupons': coupons,
#         })
    

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
                
                if CouponUser.objects.filter(user=user, status=True).exists():
                    messages.error(request, "You have already applied a coupon.")
                else:
                    
                    total = sum(item.item_total for item in cart_items)

                    if total >= coupon.min_purchase_amount:
                        CouponUser.objects.create(user=user, coupon=coupon, status=True)
                        discount = min(total, coupon.discount_amount)
                        messages.success(request, f"Coupon applied! You saved {discount}.")
                    else:
                        messages.info(request, f"The minimum purchase amount is not met for this coupon.")
            
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