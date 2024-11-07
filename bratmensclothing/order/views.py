from django.shortcuts import render,redirect,get_object_or_404
from accounts.models import Users
from products.models import ProductDetails,Category,Brand,VariantSize
from coupon.models import Coupon
from .models import Order,OrderItem
from cart.models import Cart, CartItem
from users.models import Address
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import never_cache
from django.db.models import Q
import re
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from decimal import Decimal
from django.core.paginator import Paginator
from django.urls import reverse
from coupon.models import Coupon,CouponUser


# @never_cache
# def checkout(request):
#     if request.user.is_authenticated:
#         grand_total = Decimal('0.0')
#         tax = Decimal('0.0')
#         delivery_charge = Decimal('50.0')

#         user=request.user
#         addresses=Address.objects.filter(user=user,status=False)
#         cart=get_object_or_404(Cart,user=user)
#         cart_items=CartItem.objects.filter(cart=cart)

#         total_quantity=sum(items.quantity for items in cart_items )
#         if total_quantity > 10:
#             messages.error(request, 'You have exceeded the limit of 10 items in your cart!!')
#             return redirect('cart:viewcart')
        
#         for item in cart_items:
#             if item.quantity > item.variant.qty:  
#                 messages.error(request, f"'{item.variant.product.product_name}' exceeds available stock.")
#                 return redirect('cart:viewcart')

        
#         for cart_item in cart_items:
#             variant = get_object_or_404(VariantSize, variant_id=cart_item.variant.variant_id)

#             if variant.qty == 0:
#                 messages.error(request, 'Please remove out of stock product')
#                 return redirect('cart:viewcart')


#         total = sum(items.item_total for items in cart_items)
#         tax_rate = Decimal('0.02')
#         tax = total * tax_rate
#         grand_total = total + tax + delivery_charge

#         coupons=Coupon.objects.all()
        
#         return render(request,'user/checkout.html',
#                 {
#                     'user':user,
#                     'addresses':addresses,
#                     'cart_items':cart_items,
#                     'tax':tax,
#                     'delivery_charge':delivery_charge,
#                     'grand_total':grand_total,
#                     'coupons':coupons,

#                 }) 
#     return redirect('accounts:login_user') 


@never_cache
def checkout(request):
    if request.user.is_authenticated:
        grand_total = Decimal('0.0')
        tax = Decimal('0.0')
        delivery_charge = Decimal('50.0')

        user=request.user
        addresses=Address.objects.filter(user=user,status=False)
        cart=get_object_or_404(Cart,user=user)
        cart_items=CartItem.objects.filter(cart=cart)

        total_quantity=sum(items.quantity for items in cart_items )
        if total_quantity > 10:
            messages.error(request, 'You have exceeded the limit of 10 items in your cart!!')
            return redirect('cart:viewcart')
        
        for item in cart_items:
            if item.quantity > item.variant.qty:  
                messages.error(request, f"'{item.variant.product.product_name}' exceeds available stock.")
                return redirect('cart:viewcart')

        
        for cart_item in cart_items:
            variant = get_object_or_404(VariantSize, variant_id=cart_item.variant.variant_id)

            if variant.qty == 0:
                messages.error(request, 'Please remove out of stock product')
                return redirect('cart:viewcart')


        # total = sum(items.item_total for items in cart_items)
        # tax_rate = Decimal('0.02')
        # tax = total * tax_rate
        # grand_total = total + tax + delivery_charge
        coupon_discount = Decimal('0.0')
        try:
            couponuser = CouponUser.objects.get(user=user)
            coupon_discount = couponuser.coupon.discount_amount
        
        except CouponUser.DoesNotExist:
            pass  

        total = sum(item.item_total for item in cart_items)
        total_after_discount = total - min(total, coupon_discount)
        tax_rate = Decimal('0.02')
        tax = total_after_discount * tax_rate
        grand_total = total_after_discount + tax + delivery_charge

        coupons=Coupon.objects.all()
        
        return render(request,'user/checkout.html',
                {
                    'user':user,
                    'addresses':addresses,
                    'cart_items':cart_items,
                    'tax':tax,
                    'delivery_charge':delivery_charge,
                    'grand_total':grand_total,
                    'coupons':coupons,
                    'discount':coupon_discount

                }) 
    return redirect('accounts:login_user') 



@never_cache
@login_required(login_url='accounts:login_user')
def add_address_checkout(request, userid):
    user_id = get_object_or_404(Users, userid=userid)

    if request.method == 'POST':
        address = request.POST.get('address', '').strip()
        street = request.POST.get('street', '').strip()
        landmark = request.POST.get('landmark', '').strip()
        city = request.POST.get('city', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        district = request.POST.get('district', '').strip()
        state = request.POST.get('state', '').strip()
        
        errors = {}

        # Validation logic
        if not address:
            errors['address_error'] = 'Address is required.'
        elif len(address) < 10:
            errors['address_error'] = 'Address must be at least 10 characters long.'

        if not street:
            errors['street_error'] = 'Street is required.'
        elif len(street) < 3:
            errors['street_error'] = 'Street must be at least 3 characters long.'

        if not landmark:
            errors['landmark_error'] = 'Landmark is required.'
        elif len(landmark) < 3:
            errors['landmark_error'] = 'Landmark must be at least 3 characters long.'

        if not city:
            errors['city_error'] = 'City is required.'
        elif len(city) < 3:
            errors['city_error'] = 'City must be at least 3 characters long.'

        try:
            pincode_regex = RegexValidator(regex=r'^\d{6}$', message='Pincode must be a 6-digit number.')
            pincode_regex(pincode)
        except ValidationError:
            errors['pincode_error'] = 'Pincode must be a valid 6-digit number.'

        if not state:
            errors['state_error'] = 'State is required.'
        elif len(state) < 3:
            errors['state_error'] = 'State must be at least 3 characters long.'

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        Address.objects.create(
            address=address,
            street=street,
            landmark=landmark,
            city=city,
            pincode=pincode,
            district=district,
            state=state,
            user=user_id
        )
        return JsonResponse({'success': True})

    return render(request, 'user/checkout.html', {'user': user_id})


# @never_cache
# def place_order(request):
#     if request.user.is_authenticated:
#         grand_total = Decimal('0.0')
#         tax = Decimal('0.0')
#         delivery_charge = Decimal('50.0')

#         user = request.user
#         addresses = Address.objects.filter(user=user)
#         cart = get_object_or_404(Cart, user=user)
#         cart_items = CartItem.objects.filter(cart=cart)


#         if not cart_items.exists():
#             return redirect('cart:viewcart')
            
#         total = sum(items.item_total for items in cart_items)
#         tax_rate = Decimal('0.02')
#         tax = total * tax_rate
#         grand_total = total + tax + delivery_charge

#         if request.method == 'POST':
#             selected_address_id = request.POST.get('address')
#             payment_type = request.POST.get('optradio')

#             # Check if address or payment type is missing
#             if not selected_address_id or not payment_type:
#                 messages.error(request, 'Please select an address and payment method.')
#                 return render(request, 'user/checkout.html', {
#                     'user': user,
#                     'addresses': addresses,
#                     'cart_items': cart_items,
#                     'tax': tax,
#                     'delivery_charge': delivery_charge,
#                     'grand_total': grand_total,
#                 })

#             selected_address = Address.objects.get(id=selected_address_id)

#             # Handle Cash on Delivery COD limit
#             if payment_type == 'COD' and grand_total > Decimal('1500.00'):
#                 messages.error(request, 'Cash on Delivery is not available for orders above ₹1000.')
#                 return render(request, 'user/checkout.html', {
#                     'user': user,
#                     'addresses': addresses,
#                     'cart_items': cart_items,
#                     'tax': tax,
#                     'delivery_charge': delivery_charge,
#                     'grand_total': grand_total,
#                 })

#             # Set payment status based on payment type
#             payment_status = 'Pending' if payment_type == 'COD' else 'Success'

#             # Create new order
#             new_order = Order.objects.create(
#                 user=user,
#                 shipping_address=selected_address,
#                 payment_type=payment_type,
#                 payment_status=payment_status,
#                 total_price=grand_total,
#             )

#             # Create order items and update stock
#             for item in cart_items:
#                 item_total_price = item.quantity * item.variant.price
#                 OrderItem.objects.create(
#                     order=new_order,
#                     variants=item.variant,
#                     quantity=item.quantity,
#                     price=item.variant.price,
#                     subtotal_price=item_total_price
#                 )

#                 # Deduct stock if payment successful or COD
#                 item.variant.qty -= item.quantity
#                 item.variant.save()

#             cart_items.delete()

#             return redirect('order:order_success')

#     return redirect('accounts:login_user')


@never_cache
def place_order(request):
    if request.user.is_authenticated:
        grand_total = Decimal('0.0')
        tax = Decimal('0.0')
        delivery_charge = Decimal('50.0')

        user = request.user
        addresses = Address.objects.filter(user=user)
        cart = get_object_or_404(Cart, user=user)
        cart_items = CartItem.objects.filter(cart=cart)

        if not cart_items.exists():
            return redirect('cart:viewcart')
        
        # Initialize coupon variables
        couponuser = None
        coupon_discount = Decimal('0.0')
        total = sum(item.item_total for item in cart_items)
        
        # Check for active coupon
        try:
            couponuser = CouponUser.objects.get(user=user, status=True)
            coupon_discount = couponuser.coupon.discount_amount
            total_after_discount = total - min(total, coupon_discount)
        except CouponUser.DoesNotExist:
            total_after_discount = total  # No discount if no active coupon
        
        tax_rate = Decimal('0.02')
        tax = total_after_discount * tax_rate
        grand_total = total_after_discount + tax + delivery_charge

        if request.method == 'POST':
            selected_address_id = request.POST.get('address')
            payment_type = request.POST.get('optradio')

            # Check if address or payment type is missing
            if not selected_address_id or not payment_type:
                messages.error(request, 'Please select an address and payment method.')
                return render(request, 'user/checkout.html', {
                    'user': user,
                    'addresses': addresses,
                    'cart_items': cart_items,
                    'tax': tax,
                    'delivery_charge': delivery_charge,
                    'grand_total': grand_total,
                })

            selected_address = Address.objects.get(id=selected_address_id)

            # Handle Cash on Delivery limit
            if payment_type == 'COD' and grand_total > Decimal('1500.00'):
                messages.error(request, 'Cash on Delivery is not available for orders above ₹1500.')
                return render(request, 'user/checkout.html', {
                    'user': user,
                    'addresses': addresses,
                    'cart_items': cart_items,
                    'tax': tax,
                    'delivery_charge': delivery_charge,
                    'grand_total': grand_total,
                })

            # Set payment status based payment type
            payment_status = 'Pending' if payment_type == 'COD' else 'Success'

            
            if couponuser:
                coupon = couponuser.coupon
                coupon.usage_limit -= 1
                coupon.save()  # Save the coupon 
                couponuser.status = False  
                couponuser.save() 

            # Create new order
            new_order = Order.objects.create(
                user=user,
                shipping_address=selected_address,
                payment_type=payment_type,
                payment_status=payment_status,
                total_price=grand_total,
                coupon_code=couponuser.coupon.code if couponuser else None
            )

            # Create order items and update stock
            for item in cart_items:
                item_total_price = item.quantity * item.variant.price
                OrderItem.objects.create(
                    order=new_order,
                    variants=item.variant,
                    quantity=item.quantity,
                    price=item.variant.price,
                    subtotal_price=item_total_price
                )

                # Deduct stock only if payment is successful or COD
                if payment_status == 'Success' or payment_type == 'COD':
                    item.variant.qty -= item.quantity
                    item.variant.save()

            # Empty the cart after the order
            cart_items.delete()

            return redirect('order:order_success')

    return redirect('accounts:login_user')


@never_cache
def order_success(request):
    if request.user.is_authenticated:
        return render(request,'user/ordersuccessfull.html')
    return redirect('accounts:login_user')


@never_cache
def view_orders(request):
    if request.user.is_authenticated:
        user=request.user
        orders=Order.objects.filter(user=user)
        order_items=OrderItem.objects.filter(order__in=orders)

        return render(request,'user/order_details.html',
                      {
                        'orders':orders,
                        'order_items':order_items,
                    })
    
    return redirect('accounts:login_user')
    


@never_cache
def manage_orders(request, orderitem_id):
    if request.user.is_authenticated:
        

        tax_rate = Decimal('0.02')
        delivery_charge = Decimal('50.0')

        try:
            orderitem = OrderItem.objects.get(orderitem_id=orderitem_id)
            if request.user.userid != orderitem.order.user.userid:  
                return redirect('userss:error')


            item_price = Decimal(orderitem.price)
            item_quantity = Decimal(orderitem.quantity)  
            item_tax = item_price * tax_rate * item_quantity 

            return render(request, 'user/manageorder.html', 
                          {'orderitem': orderitem,
                           'tax':item_tax,
                           'delivery_charge':delivery_charge
                           })
        
        except OrderItem.DoesNotExist:
            return render(request, 'user/manageorder.html', {'error': 'Order item not found.'})

    return redirect('accounts:login_user')


def cancel_order(request, orderitem_id):
    item = get_object_or_404(OrderItem, orderitem_id=orderitem_id) 

    if item.variants:  
        item.variants.qty += item.quantity 
        item.variants.save() 

    item.status = 'Cancelled'
    item.save() 

    messages.success(request, 'Your order has been cancelled successfully.')

    return redirect('order:view_orders')


def is_staff(user):
    return user.is_staff

@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff, login_url='accounts:admin_login')
def order_details(request):
    orders = OrderItem.objects.all().order_by('-orderitem_id')
    paginator = Paginator(orders, 4)  

    page_number = request.GET.get('page') 
    orders = paginator.get_page(page_number)  

    if request.method == 'POST':
        order_id = request.POST.get('order_id')  
        action = request.POST.get('status')

        if order_id and action:
            order = get_object_or_404(OrderItem, orderitem_id=order_id)  
            order.status = action  
            order.variants.qty += order.quantity 
            order.save() 

            return redirect('order:order_details') 

    return render(request, 'admin/orders.html', {'orders': orders}) 