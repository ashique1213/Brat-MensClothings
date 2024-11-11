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
from offer.models import Product_Offers,Brand_Offers
from django.utils import timezone
import razorpay
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from wallet.models import Wallet,Transaction
from django.db.models import Sum, F



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
            couponuser = CouponUser.objects.get(user=user,status=True)
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




            if payment_type == 'Razorpay':
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                
                payment_data = {
                    "amount": int(float(grand_total) * 100), 
                    "currency": "INR", 
                    "payment_capture": 1
                }
                
                try:
                    razorpay_order = client.order.create(data=payment_data)
                except razorpay.errors.BadRequestError:
                    messages.error(request, 'Error creating Razorpay order. Please try again.')
                    return redirect('order:checkout')

                request.session['pending_order_details'] = {
                    "user": user.userid,
                    "shipping_address": selected_address.id,
                    "payment_type": payment_type,
                    "total_price":float(grand_total), 
                    "coupon_code": couponuser.coupon.code if couponuser else None, 
                    "coupon_amount":int(float(couponuser.coupon.discount_amount)) if couponuser else None
                    

                }

                return render(request, 'user/payment.html', {
                    "razorpay_order_id": razorpay_order['id'],
                    "razorpay_key_id": settings.RAZORPAY_KEY_ID,
                    "amount": payment_data["amount"]
                })
          
            # Handle Cash on Delivery 
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
                coupon_code=couponuser.coupon.code if couponuser else None,
                coupon_amount=couponuser.coupon.discount_amount if couponuser else None
            )

            # Create order items and update stock
            for item in cart_items:
                item_total_price = item.quantity * item.variant.product.price
                OrderItem.objects.create(
                    order=new_order,
                    variants=item.variant,
                    quantity=item.quantity,
                    price=item.variant.product.price,
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


@csrf_exempt
@never_cache
def verify_payment(request):
    if request.user.is_authenticated:

        if request.method == "POST":
            payment_data = json.loads(request.body.decode('utf-8'))
            params_dict = {
                'razorpay_order_id': payment_data.get('razorpay_order_id'),
                'razorpay_payment_id': payment_data.get('razorpay_payment_id'),
                'razorpay_signature': payment_data.get('razorpay_signature')
            }
            
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            try:
                client.utility.verify_payment_signature(params_dict)

                order_data = request.session.get('pending_order_details')
                if not order_data:
                    return JsonResponse({'error': 'Order details not found in session.'}, status=400)

                user_id = order_data.get("user")
                shipping_address_id = order_data.get("shipping_address")
                total_price = order_data.get("total_price")
                coupon_code = order_data.get("coupon_code")
                coupon_amount = order_data.get("coupon_amount")
               
                user = get_object_or_404(Users, userid=user_id)
                shipping_address = get_object_or_404(Address, id=shipping_address_id)

                # Use an atomic transaction for order and stock updates
                with transaction.atomic():
                    # Create and save the order
                    new_order = Order.objects.create(
                        user=user,
                        shipping_address=shipping_address,
                        payment_type='Razorpay',
                        payment_status='Success',
                        total_price=total_price,
                        coupon_code=coupon_code,
                        coupon_amount=coupon_amount
                        
                    )

                    # Retrieve cart and create order items
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

                    for item in cart_items:
                        OrderItem.objects.create(
                            order=new_order,
                            variants=item.variant,
                            quantity=item.quantity,
                            price=item.variant.product.price,
                            subtotal_price=item.quantity * item.variant.product.price
                        )

                        # Deduct stock
                        item.variant.qty -= item.quantity
                        item.variant.save()

                    # Clear the cart
                    cart_items.delete()
                    del request.session['pending_order_details']

                return JsonResponse({'message': 'Order placed successfully!'})

            except razorpay.errors.SignatureVerificationError:
                return JsonResponse({'error': 'Payment verification failed.'}, status=400)
            except Exception as e:
                # Log exception and return error
                print(f"Order creation failed: {e}")
                return JsonResponse({'error': 'An error occurred while placing the order.'}, status=500)

        return JsonResponse({'error': 'Invalid request method.'}, status=405)

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
        order_items=OrderItem.objects.filter(order__in=orders).order_by('-order')

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


            item_price = Decimal(orderitem.variants.product.price)
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
    user = item.order.user

    if item.order.payment_status=='Success':
        order = item.order 
        
        total_quantity = Decimal(OrderItem.objects.filter(order=order).aggregate(total_qty=Sum('quantity'))['total_qty'] or 0)
        item_quantity = Decimal(item.quantity)  


        new_price = Decimal(item.price) * Decimal(item_quantity)

        if order.coupon_amount and total_quantity:
            new_price -= Decimal(order.coupon_amount) / Decimal(total_quantity)
        
        user_wallet, created = Wallet.objects.get_or_create(user_id=user)

        user_wallet.balance = Decimal(user_wallet.balance or 0) + new_price
        user_wallet.save()
        
        details_text = f"Tracking: {order.tracking_number}, Product: {item.variants.product.product_name}"
        Transaction.objects.create(
            wallet_id=user_wallet,
            transaction_type='Order Cancellation',
            amount=new_price,
            details=details_text
        )
    
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
        ALLOWED_TRANSITIONS = {
            "Order Pending": ["Order Confirmed", "Cancelled"],
            "Order Confirmed": ["Shipped", "Cancelled"],
            "Shipped": ["Out For Delivery", "Cancelled"],
            "Out For Delivery": ["Delivered"],
            "Delivered": ["Requested Return"],
            "Requested Return": ["Approve Returned", "Reject Returned"],
            "Approve Returned": [],
            "Reject Returned": [],
            "Cancelled": [],
        }
        order_id = request.POST.get('order_id')  
        action = request.POST.get('status')

        if order_id and action:
            order = get_object_or_404(OrderItem, orderitem_id=order_id)  
            current_status = order.status
            print(F'{current_status}')
            if action in ALLOWED_TRANSITIONS.get(current_status, []):
                order.status = action 
                if action == 'Cancelled':
                
                    variant = order.variants  
                    variant.qty += order.quantity  
                    variant.save()  
                
                order.save() 
                messages.success(request, f"Order status updated to {action}.")
                return redirect('order:order_details') 
            else:
                messages.error(request, f"Invalid status transition from {current_status} to {action}.")

            return redirect('order:order_details')

    return render(request, 'admin/orders.html', {'orders': orders}) 



def return_order(request, orderitem_id):
    item = get_object_or_404(OrderItem, orderitem_id=orderitem_id) 
    item.status = 'Requested Return'
    item.save()
    
    messages.success(request, 'Your order has been returned successfully.')
    return redirect('order:view_orders')