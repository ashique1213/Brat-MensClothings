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
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import DatabaseError
import logging
logger = logging.getLogger('order.views')

@never_cache
def checkout(request):
    logger.debug("checkout view called | user=%s | authenticated=%s", request.user, request.user.is_authenticated)

    if request.user.is_authenticated:
        try:
            grand_total = Decimal('0.0')
            tax = Decimal('0.0')
            delivery_charge = getattr(settings, 'DELIVERY_CHARGE', Decimal('50'))

            user = request.user
            logger.debug("Checkout processing | user_id=%s", user.userid)
            addresses = Address.objects.filter(user=user, status=False)
            cart = get_object_or_404(Cart, user=user)
            cart_items = CartItem.objects.filter(cart=cart)
            logger.debug("Cart loaded | cart_id=%s | items_count=%d", cart.id, cart_items.count())
            for cart_item in cart_items:
                variant = cart_item.variant
                product = variant.product

                if product.is_deleted or product.brand.is_deleted:
                    logger.warning("Unavailable product in cart | product_id=%s | user_id=%s", product.product_id, user.userid)
                    messages.error(request, "Please remove unavailable products from your cart.")
                    return redirect('cart:viewcart')

                for category in product.category.all():
                    if category.is_deleted:
                        logger.warning("Product in deleted category | product_id=%s | category_id=%s", product.product_id, category.category_id)
                        messages.error(request, "Please remove products from deleted categories.")
                        return redirect('cart:viewcart')

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
                    logger.debug("Product offer applied | product_id=%s | discount=%s", product.product_id, product_offer.offer_price)
                if brand_offer:
                    brand_discounted_price = product.price - brand_offer.offer_price
                    discounted_price = min(discounted_price, brand_discounted_price)
                    logger.debug("Brand offer applied | brand_id=%s | discount=%s", product.brand.brand_id, brand_offer.offer_price)

                cart_item.variant.product.price = discounted_price

            total_quantity = sum(items.quantity for items in cart_items)
            if total_quantity > 10:
                messages.error(request, 'You have exceeded the limit of 10 items in your cart.')
                return redirect('cart:viewcart')

            for item in cart_items:
                if item.quantity > item.variant.qty:
                    messages.error(request, f"'{item.variant.product.product_name}' exceeds available stock.")
                    return redirect('cart:viewcart')

                variant = get_object_or_404(VariantSize, variant_id=item.variant.variant_id)
                if variant.qty == 0:
                    messages.error(request, 'Please remove out-of-stock products from your cart.')
                    return redirect('cart:viewcart')

            coupon_discount = Decimal('0.0')
            try:
                couponuser = CouponUser.objects.get(user=user, status=True)
                coupon_discount = couponuser.coupon.discount_amount
            except CouponUser.DoesNotExist:
                logger.debug("No active coupon for user | user_id=%s", user.userid)
                pass
            except Exception as e:
                logger.error("Error applying coupon | user_id=%s | error=%s", user.userid, e, exc_info=True)
                messages.error(request, "An error occurred while applying the coupon.")
                return redirect('cart:viewcart')

            total = sum(item.item_total for item in cart_items)
            total_after_discount = total - min(total, coupon_discount)
            tax_rate = getattr(settings, 'TAX_RATE', Decimal('0.02'))
            tax = total_after_discount * tax_rate
            grand_total = total_after_discount + tax + delivery_charge
            limit = getattr(settings, 'DISCOUNT_LIMIT', Decimal('1000'))

            coupons = Coupon.objects.all()
            try:
                user_wallet = Wallet.objects.get(user_id=user)
                wallet_balance = user_wallet.balance
                logger.debug("Wallet loaded | user_id=%s | balance=%s", user.userid, wallet_balance)
            except Wallet.DoesNotExist:
                wallet_balance = Decimal('0.0')
                logger.debug("No wallet found | user_id=%s", user.userid)
            except Exception as e:
                wallet_balance = Decimal('0.0')
                logger.error("Error loading wallet | user_id=%s | error=%s", user.userid, e, exc_info=True)

            return render(request, 'user/checkout.html', {
                'user': user,
                'addresses': addresses,
                'cart_items': cart_items,
                'tax': tax,
                'delivery_charge': delivery_charge,
                'grand_total': grand_total,
                'coupons': coupons,
                'discount': coupon_discount,
                'limit': limit,
                'wallet_balance': wallet_balance,
                'total': total
            })

        except DatabaseError as e:
            logger.error("Database error in checkout | user_id=%s | error=%s", user.userid, e, exc_info=True)
            messages.error(request, "An error occurred while processing your checkout. Please try again.")
            return redirect('cart:viewcart')
        except Exception as e:
            logger.error("Unexpected error in checkout | user_id=%s | error=%s", user.userid, e, exc_info=True)
            messages.error(request, "An unexpected error occurred. Please contact support.")
            return redirect('cart:viewcart')

    return redirect('accounts:login_user') 


@never_cache
def place_order(request):
    logger.debug("place_order called | user=%s | method=%s", request.user, request.method)
    if request.user.is_authenticated:
        try:
            grand_total = Decimal('0.0')
            tax = Decimal('0.0')
            delivery_charge = getattr(settings, 'DELIVERY_CHARGE', Decimal('50'))

            user = request.user
            addresses = Address.objects.filter(user=user)
            cart = get_object_or_404(Cart, user=user)
            cart_items = CartItem.objects.filter(cart=cart)

            if not cart_items.exists():
                logger.warning("Empty cart on place_order | user_id=%s", user.userid)
                messages.error(request, 'Your cart is empty.')
                return redirect('cart:viewcart')

            total_offer_discount = Decimal('0.0')
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
                    total_offer_discount += product_offer.offer_price
                if brand_offer:
                    brand_discounted_price = product.price - brand_offer.offer_price
                    total_offer_discount += brand_offer.offer_price
                    discounted_price = min(discounted_price, brand_discounted_price)

                cart_item.variant.product.price = discounted_price

            couponuser = None
            coupon_discount = Decimal('0.0')
            total = sum(item.item_total for item in cart_items)
            try:
                couponuser = CouponUser.objects.get(user=user, status=True)
                coupon_discount = couponuser.coupon.discount_amount
                total_after_discount = total - min(total, coupon_discount)
            except CouponUser.DoesNotExist:
                total_after_discount = total
            except Exception as e:
                total_after_discount = total
                logger.error("Coupon error in place_order | user_id=%s | error=%s", user.userid, e)

            tax_rate = getattr(settings, 'TAX_RATE', Decimal('0.02'))
            tax = total_after_discount * tax_rate
            grand_total = total_after_discount + tax + delivery_charge

            if request.method == 'POST':
                selected_address_id = request.POST.get('address')
                payment_type = request.POST.get('optradio')
                logger.debug("Order placement | address_id=%s | payment_type=%s", selected_address_id, payment_type)

                if not selected_address_id or not payment_type:
                    messages.error(request, 'Please select an address and payment method.')
                    return redirect('order:checkout')

                try:
                    selected_address = Address.objects.get(id=selected_address_id)
                except Address.DoesNotExist:
                    logger.warning("Invalid address selected | address_id=%s", selected_address_id)
                    messages.error(request, 'Selected address not found.')
                    return redirect('order:checkout')

                if payment_type == 'Razorpay':
                    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                    payment_data = {
                        "amount": int(float(grand_total) * 100),
                        "currency": "INR",
                        "payment_capture": 1
                    }

                    try:
                        razorpay_order = client.order.create(data=payment_data)
                        request.session['pending_order_details'] = {
                            "user": user.userid,
                            "shipping_address": selected_address.id,
                            "payment_type": payment_type,
                            "total_price": float(grand_total),
                            "coupon_code": couponuser.coupon.code if couponuser else 0,
                            "coupon_amount": int(float(couponuser.coupon.discount_amount)) if couponuser else 0,
                            "total_offer_discount": float(total_offer_discount) if total_offer_discount else 0,
                        }
                        logger.info("Razorpay order created | razorpay_order_id=%s | amount=%s", razorpay_order['id'], payment_data["amount"])
                        return render(request, 'user/payment.html', {
                            "razorpay_order_id": razorpay_order['id'],
                            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
                            "amount": payment_data["amount"]
                        })
                    except razorpay.errors.BadRequestError as e:
                        logger.error("Razorpay order creation failed | error=%s", e)
                        messages.error(request, 'Error creating Razorpay order. Please try again.')
                        return redirect('order:checkout')
                    except Exception as e:
                        logger.error("Unexpected error in Razorpay | error=%s", e)
                        messages.error(request, 'An unexpected error occurred during payment processing.')
                        return redirect('order:checkout')

                if payment_type == 'Wallet':
                    try:
                        user_wallet = Wallet.objects.get(user_id=user)
                        if user_wallet.balance < grand_total:
                            logger.warning("Insufficient wallet balance | user_id=%s | balance=%s | required=%s", user.userid, user_wallet.balance, grand_total)
                            messages.error(request, 'Insufficient wallet balance to place the order.')
                            return redirect('order:checkout')

                        with transaction.atomic():
                            user_wallet.balance = Decimal(user_wallet.balance) - Decimal(grand_total)
                            user_wallet.save()

                            if couponuser:
                                coupon = couponuser.coupon
                                coupon.usage_limit -= 1
                                coupon.save()
                                couponuser.status = False
                                couponuser.save()

                            new_order = Order.objects.create(
                                user=user,
                                shipping_address=selected_address,
                                payment_type=payment_type,
                                payment_status='Success',
                                total_price=grand_total,
                                coupon_code=couponuser.coupon.code if couponuser else 0,
                                coupon_amount=couponuser.coupon.discount_amount if couponuser else 0,
                                total_offer_discount=total_offer_discount if total_offer_discount else 0
                            )
                            logger.info("Wallet order created | order_id=%s | user_id=%s", new_order.order_id, user.userid)

                            Transaction.objects.create(
                                wallet_id=user_wallet,
                                transaction_type='Debited',
                                amount=grand_total,
                                details="Wallet Payment for Order"
                            )

                            for item in cart_items:
                                item_total_price = item.quantity * item.variant.product.price
                                OrderItem.objects.create(
                                    order=new_order,
                                    variants=item.variant,
                                    quantity=item.quantity,
                                    price=item.variant.product.price,
                                    subtotal_price=item_total_price
                                )
                                item.variant.qty -= item.quantity
                                item.variant.save()

                            cart_items.delete()
                            logger.info("Wallet order completed successfully | order_id=%s", new_order.order_id)
                            return redirect('order:order_success')

                    except Wallet.DoesNotExist:
                        logger.warning("Wallet not found for user | user_id=%s", user.userid)
                        messages.error(request, 'Wallet not found. Please try another payment method.')
                        return redirect('order:checkout')
                    except DatabaseError as e:
                        logger.error("DB error in wallet payment | error=%s", e)
                        messages.error(request, 'Error processing wallet payment. Please try again.')
                        return redirect('order:checkout')
                    except Exception as e:
                        logger.error("Unexpected error in wallet payment | error=%s", e)
                        messages.error(request, 'An unexpected error occurred during wallet payment.')
                        return redirect('order:checkout')

                if payment_type == 'COD' and grand_total > Decimal('1000.00'):
                    logger.warning("COD not allowed for high amount | amount=%s", grand_total)
                    messages.error(request, 'Cash on Delivery is not available for orders above ₹1000.')
                    return redirect('order:checkout')

                payment_status = 'Pending' if payment_type == 'COD' else 'Success'

                try:
                    with transaction.atomic():
                        if couponuser:
                            coupon = couponuser.coupon
                            coupon.usage_limit -= 1
                            coupon.save()
                            couponuser.status = False
                            couponuser.save()

                        new_order = Order.objects.create(
                            user=user,
                            shipping_address=selected_address,
                            payment_type=payment_type,
                            payment_status=payment_status,
                            total_price=grand_total,
                            coupon_code=couponuser.coupon.code if couponuser else 0,
                            coupon_amount=couponuser.coupon.discount_amount if couponuser else 0,
                            total_offer_discount=total_offer_discount if total_offer_discount else 0
                        )
                        logger.info("Order created | order_id=%s | payment_type=%s | status=%s", new_order.order_id, payment_type, payment_status)

                        for item in cart_items:
                            item_total_price = item.quantity * item.variant.product.price
                            OrderItem.objects.create(
                                order=new_order,
                                variants=item.variant,
                                quantity=item.quantity,
                                price=item.variant.product.price,
                                subtotal_price=item_total_price
                            )
                            if payment_status == 'Success' or payment_type == 'COD':
                                item.variant.qty -= item.quantity
                                item.variant.save()

                        cart_items.delete()
                        logger.info("Order placement successful | order_id=%s", new_order.order_id)
                        return redirect('order:order_success')

                except DatabaseError as e:
                    logger.error("DB error creating order | error=%s", e)
                    messages.error(request, 'Error creating order. Please try again.')
                    return redirect('order:checkout')
                except Exception as e:
                    logger.error("Unexpected error placing order | error=%s", e)
                    messages.error(request, 'An unexpected error occurred while placing the order.')
                    return redirect('order:checkout')

        except DatabaseError as e:
            logger.error("Database error in place_order | error=%s", e)
            messages.error(request, 'Error processing your order. Please try again.')
            return redirect('cart:viewcart')
        except Exception as e:
            logger.error("Unexpected error in place_order | error=%s", e)
            messages.error(request, 'An unexpected error occurred. Please contact support.')
            return redirect('cart:viewcart')

    return redirect('accounts:login_user')


@csrf_exempt
@never_cache
def verify_payment(request):
    logger.debug("verify_payment called | method=%s", request.method)
    if request.user.is_authenticated:
        try:
            if request.method != "POST":
                logger.warning("Invalid method for verify_payment | method=%s", request.method)
                return JsonResponse({'error': 'Invalid request method.'}, status=405)

            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_signature = request.POST.get('razorpay_signature')

            if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
                logger.warning("Missing payment details in verify_payment")
                return JsonResponse({'error': 'Missing payment details.'}, status=400)

            order_data = request.session.get('pending_order_details')
            if not order_data:
                logger.warning("No pending order in session")
                return JsonResponse({'error': 'Order details not found in session.'}, status=400)

            user_id = order_data.get("user")
            shipping_address_id = order_data.get("shipping_address")
            total_price = order_data.get("total_price")
            coupon_code = order_data.get("coupon_code")
            coupon_amount = order_data.get("coupon_amount")
            total_offer_discount = order_data.get("total_offer_discount")

            try:
                user = get_object_or_404(Users, userid=user_id)
                shipping_address = get_object_or_404(Address, id=shipping_address_id)
            except Exception as e:
                logger.error("Invalid user or address in session | error=%s", e)
                return JsonResponse({'error': 'Invalid user or address.'}, status=400)

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }

            payment_status = 'Failure'
            try:
                client.utility.verify_payment_signature(params_dict)
                payment_status = 'Success'
                logger.info("Razorpay signature verified | payment_id=%s", razorpay_payment_id)
            except razorpay.errors.SignatureVerificationError as e:
                logger.warning("Razorpay signature verification failed | payment_id=%s", razorpay_payment_id)
                payment_status = 'Failure'

            couponuser = None
            if coupon_code:
                try:
                    couponuser = CouponUser.objects.filter(user=user, coupon__code=coupon_code, status=True).first()
                    if couponuser:
                        coupon = couponuser.coupon
                        coupon.usage_limit -= 1
                        coupon.save()
                        couponuser.status = False
                        couponuser.save()
                        logger.info("Coupon invalidated after payment | code=%s", coupon_code)
                except Exception as e:
                    logger.error("Error invalidating coupon | error=%s", e)
                    messages.error(request, 'Error applying coupon during payment verification.')

            try:
                with transaction.atomic():
                    new_order = Order.objects.create(
                        user=user,
                        shipping_address=shipping_address,
                        payment_type='Razorpay',
                        payment_status=payment_status,
                        total_price=total_price,
                        coupon_code=coupon_code,
                        coupon_amount=coupon_amount,
                        total_offer_discount=total_offer_discount
                    )
                    logger.info("Order created from Razorpay | order_id=%s | status=%s", new_order.order_id, payment_status)

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

                        OrderItem.objects.create(
                            order=new_order,
                            variants=cart_item.variant,
                            quantity=cart_item.quantity,
                            price=cart_item.variant.product.price,
                            subtotal_price=cart_item.quantity * cart_item.variant.product.price
                        )
                        cart_item.variant.qty -= cart_item.quantity
                        cart_item.variant.save()

                    cart_items.delete()
                    if 'pending_order_details' in request.session:
                        del request.session['pending_order_details']
                        logger.debug("Session cleared after order")
                
                logger.info("Razorpay order processed successfully | order_id=%s", new_order.order_id)
                return redirect('order:order_success')

            except DatabaseError as e:
                logger.error("DB error in verify_payment | error=%s", e)
                return JsonResponse({'error': 'Error processing order. Please try again.'}, status=500)
            except Exception as e:
                logger.error("Unexpected error in verify_payment | error=%s", e)
                return JsonResponse({'error': 'An unexpected error occurred during payment processing.'}, status=500)

        except Exception as e:
            logger.error("Critical error in verify_payment | error=%s", e)
            return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)

    return redirect('accounts:login_user')


@never_cache
def retry_payment(request, order_id):
    logger.debug("retry_payment called | order_id=%s", order_id)
    if request.user.is_authenticated:
        order = get_object_or_404(Order, order_id=order_id)
        
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Create a Razorpay order
        razorpay_order = client.order.create({
            "amount": int(order.total_price * 100),  
            "currency": "INR",
            "payment_capture": "1"  
        })
        logger.info("Retry Razorpay order created | order_id=%s | razorpay_order_id=%s", order_id, razorpay_order['id'])
        
        
        context = {
            "order": order,
            "razorpay_order_id": razorpay_order['id'],
            "razorpay_key": settings.RAZORPAY_KEY_ID,  
            "amount": order.total_price * 100,  
        }
        
        return render(request, 'user/retry_payment.html', context)
    
    return redirect('accounts:login_user')


@never_cache
def verify_retry_payment(request):
    logger.debug("verify_retry_payment called | method=%s", request.method)
    if request.user.is_authenticated:
        if request.method == 'POST':
            user=request.user
            orders=Order.objects.filter(user=user)
            order_items=OrderItem.objects.filter(order__in=orders).order_by('-order')
            
            order_id = request.POST.get('order_id')
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_signature = request.POST.get('razorpay_signature')

            order = Order.objects.get(order_id=order_id)
            
            order_item = OrderItem.objects.filter(order_id=order_id)


            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            # Verify the payment signature
            params = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            }

            try:
                client.utility.verify_payment_signature(params)

                order.payment_status = 'Success'
                order.save()

                for item in order_item:
                    item.status="Order confirmed"
                    item.save()
                
                logger.info("Retry payment successful | order_id=%s | payment_id=%s", order_id, razorpay_payment_id)
                return redirect('order:order_success')

            except razorpay.errors.SignatureVerificationError:
                logger.warning("Retry payment failed | order_id=%s | payment_id=%s", order_id, razorpay_payment_id)
                messages.success(request, 'Payment again failed')
                return render(request, 'user/order_details.html', {'order': order,'order_items':order_items,'orders':orders})

        else:
            return redirect('order:order_details') 
        
    return redirect('accounts:login_user')



@never_cache
def order_success(request):
    logger.debug("order_success page accessed | user=%s", request.user)
    if request.user.is_authenticated:
        return render(request,'user/ordersuccessfull.html')
    return redirect('accounts:login_user')


@never_cache
def view_orders(request):
    logger.debug("view_orders called | user=%s", request.user)
    if request.user.is_authenticated:
        user=request.user
        orders=Order.objects.filter(user=user)

        order_items=OrderItem.objects.filter(order__in=orders).order_by('-order')


        paginator = Paginator(order_items, 4)

        page_number = request.GET.get('page')

        try:
            page_obj = paginator.get_page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.get_page(1)
        except EmptyPage:
            page_obj = paginator.get_page(paginator.num_pages)

        logger.info("Orders page rendered | user_id=%s | orders_count=%d", user.userid, orders.count())
        return render(request,'user/order_details.html',
                      {
                        'orders':orders,
                        # 'order_items':order_items,
                        'order_items': page_obj, 
                        'page_obj': page_obj  
                    })
    
    return redirect('accounts:login_user')
    


@never_cache
def manage_orders(request, orderitem_id):
    logger.debug("manage_orders called | orderitem_id=%s", orderitem_id)
    if request.user.is_authenticated:
        

        tax_rate = getattr(settings, 'TAX_RATE', Decimal('0.02'))
        delivery_charge = getattr(settings, 'DELIVERY_CHARGE', Decimal('50'))

        try:
            orderitem = OrderItem.objects.get(orderitem_id=orderitem_id)
            if request.user.userid != orderitem.order.user.userid:  
                return redirect('userss:error')


            item_price = Decimal(orderitem.variants.product.price)
            item_quantity = Decimal(orderitem.quantity)  
            item_tax = item_price * tax_rate * item_quantity 

            logger.info("Manage order page rendered | orderitem_id=%s", orderitem_id)
            return render(request, 'user/manageorder.html', 
                          {'orderitem': orderitem,
                           'tax':item_tax,
                           'delivery_charge':delivery_charge
                           })
        
        except OrderItem.DoesNotExist:
            logger.warning("Order item not found | orderitem_id=%s", orderitem_id)
            return render(request, 'user/manageorder.html', {'error': 'Order item not found.'})

    return redirect('accounts:login_user')


def cancel_order(request, orderitem_id):
    logger.debug("cancel_order called | orderitem_id=%s", orderitem_id)
    try:
        item = get_object_or_404(OrderItem, orderitem_id=orderitem_id)
        user = item.order.user
        order = item.order

        with transaction.atomic():
            if order.payment_status == 'Success':
                total_order_value_before_cancellation = Decimal(order.total_price)
                total_order_value_after_cancellation = total_order_value_before_cancellation - Decimal(item.subtotal_price)

                coupon_applied = None
                if order.coupon_code:
                    try:
                        coupon_applied = Coupon.objects.filter(code=order.coupon_code).first()
                    except Exception as e:
                        pass

                try:
                    user_wallet, _ = Wallet.objects.get_or_create(user_id=user)
                except Exception as e:
                    logger.error("Wallet error in cancel | error=%s", e)
                    messages.error(request, 'Error processing refund. Please contact support.')
                    return redirect('order:view_orders')

                if order.items.filter(status='Cancelled').count() + 1 == order.items.count():
                    full_refund_amount = order.total_price
                    user_wallet.balance = Decimal(user_wallet.balance or 0) + full_refund_amount
                    user_wallet.save()

                    try:
                        Transaction.objects.create(
                            wallet_id=user_wallet,
                            transaction_type='Full Refund',
                            amount=full_refund_amount,
                            details="Order Cancelled: Full Refund including tax and delivery charges"
                        )
                        logger.info("Full refund issued | order_id=%s | amount=%s", order.order_id, full_refund_amount)
                    except Exception as e:
                        messages.error(request, 'Error recording refund transaction.')
                        return redirect('order:view_orders')

                    order.total_price = Decimal(0)
                    order.coupon_amount = Decimal(0)
                    order.save()
                else:
                    if item.subtotal_price > 0:
                        user_wallet.balance = Decimal(user_wallet.balance or 0) + Decimal(item.subtotal_price)
                        user_wallet.save()

                        try:
                            Transaction.objects.create(
                                wallet_id=user_wallet,
                                transaction_type='Item Refund',
                                amount=Decimal(item.subtotal_price),
                                details=f"Order Cancelled: {item.variants.product.product_name}, Item Refund"
                            )
                            logger.info("Item refund | orderitem_id=%s | amount=%s", orderitem_id, item.subtotal_price)
                        except Exception as e:
                            messages.error(request, 'Error recording refund transaction.')
                            return redirect('order:view_orders')

                    if coupon_applied and total_order_value_after_cancellation < coupon_applied.min_purchase_amount:
                        order.coupon_amount = Decimal(0)

                    order.total_price = total_order_value_after_cancellation
                    order.save()

                if item.variants:
                    item.variants.qty += item.quantity
                    item.variants.save()

                item.status = 'Cancelled'
                item.save()

                if order.items.filter(status='Cancelled').count() == order.items.count():
                    full_refund_amount = order.total_price
                    if full_refund_amount > 0:
                        user_wallet.balance = Decimal(user_wallet.balance or 0) + full_refund_amount
                        user_wallet.save()

                        try:
                            Transaction.objects.create(
                                wallet_id=user_wallet,
                                transaction_type='Order cancellation',
                                amount=full_refund_amount,
                                details="Order Tax and Delivery charge"
                            )
                        except Exception as e:
                            logger.info("Order item cancelled | orderitem_id=%s", orderitem_id)
                            messages.error(request, 'Error recording refund transaction.')
                            return redirect('order:view_orders')

                        order.total_price = Decimal(0)
                        order.save()

            elif order.payment_status == 'Pending':
                if item.variants:
                    item.variants.qty += item.quantity
                    item.variants.save()

                item.status = 'Cancelled'
                item.save()

                if order.items.count() > 1:
                    order.total_price -= item.subtotal_price
                    order.save()

            else:
                order.payment_status = 'Pending'
                order.save()
                if item.variants:
                    item.variants.qty += item.quantity
                    item.variants.save()

                item.status = 'Cancelled'
                item.save()

                if order.items.count() > 1:
                    order.total_price -= item.subtotal_price
                    order.save()

            messages.success(request, 'Your order has been cancelled successfully.')
            return redirect('order:view_orders')

    except OrderItem.DoesNotExist:
        logger.warning("Order item not found in cancel | orderitem_id=%s", orderitem_id)
        messages.error(request, 'Order item not found.')
        return redirect('order:view_orders')
    except DatabaseError as e:
        logger.error("DB error in cancel_order | error=%s", e)
        messages.error(request, 'Error cancelling order. Please try again.')
        return redirect('order:view_orders')
    except Exception as e:
        logger.error("Unexpected error in cancel_order | error=%s", e)
        messages.error(request, 'An unexpected error occurred while cancelling the order.')
        return redirect('order:view_orders')



def is_staff(user):
    return user.is_staff


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff, login_url='accounts:admin_login')
def order_details(request):
    logger.debug("admin order_details called | admin=%s", request.user)
    search_query=request.GET.get('search','') 

    if search_query:
        orders = OrderItem.objects.filter(
            Q(order__tracking_number__icontains=search_query) | 
            Q(order__user__userid__icontains=search_query)
        ).order_by('-orderitem_id')
        logger.info("Admin order search | query='%s' | results=%d", search_query, orders.count())
    else:
        orders = OrderItem.objects.all().order_by('-orderitem_id')
        logger.debug("All admin orders loaded | count=%d", orders.count())
    
    paginator = Paginator(orders, 4)  
    page_number = request.GET.get('page') 
    orders = paginator.get_page(page_number)  
    logger.debug("Admin orders paginated | page=%s | total_pages=%d", orders.number, paginator.num_pages)

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
        logger.debug("Admin POST status update | orderitem_id=%s | action=%s", order_id, action)

        if order_id and action:
            order = get_object_or_404(OrderItem, orderitem_id=order_id)  
            current_status = order.status
            logger.debug("Current status check | orderitem_id=%s | current=%s", order_id, current_status)

            if action in ALLOWED_TRANSITIONS.get(current_status, []):
                order.status = action 
                logger.info("Admin status update | orderitem_id=%s | from=%s | to=%s", order_id, current_status, action)

                if action == 'Cancelled':
                    logger.info("Admin initiated cancellation | orderitem_id=%s", order_id)
                    item = get_object_or_404(OrderItem, orderitem_id=order_id)
                    user = item.order.user
                    order = item.order

                    if order.payment_status == 'Success':
                        logger.debug("Processing refund for paid order | order_id=%s", order.order_id)
                        total_order_value_before_cancellation = Decimal(order.total_price)
                        total_order_value_after_cancellation = total_order_value_before_cancellation - Decimal(item.subtotal_price)

                        coupon_applied = None
                        if order.coupon_code:
                            coupon_applied = Coupon.objects.filter(code=order.coupon_code).first()

                        user_wallet, _ = Wallet.objects.get_or_create(user_id=user)
                        logger.debug("Wallet ready | user_id=%s | current_balance=%s", user.userid, user_wallet.balance)

                        # Detect single product order
                        if order.items.filter(status='Cancelled').count() + 1 == order.items.count():
                            # Single product: Refund full order value
                            full_refund_amount = order.total_price
                            user_wallet.balance = Decimal(user_wallet.balance or 0) + full_refund_amount
                            user_wallet.save()

                            Transaction.objects.create(
                                wallet_id=user_wallet,
                                transaction_type='Full Refund',
                                amount=full_refund_amount,
                                details="Order Cancelled: Full Refund including tax and delivery charges"
                            )
                            logger.info("Full refund processed | order_id=%s | amount=%s", order.order_id, full_refund_amount)

                            # Reset order total_price and coupon
                            order.total_price = Decimal(0)
                            order.coupon_amount = Decimal(0)
                            order.save()
                        else:
                            # Multi-product: Adjust price and refund only the item subtotal
                            if item.subtotal_price > 0:
                                user_wallet.balance = Decimal(user_wallet.balance or 0) + Decimal(item.subtotal_price)
                                user_wallet.save()

                                Transaction.objects.create(
                                    wallet_id=user_wallet,
                                    transaction_type='Item Refund',
                                    amount=Decimal(item.subtotal_price),
                                    details=f"Order Cancelled: {item.variants.product.product_name}, Item Refund"
                                )
                                logger.info("Item refund processed | orderitem_id=%s | amount=%s", item.orderitem_id, item.subtotal_price)

                            # Adjust for coupon violation
                            if coupon_applied and total_order_value_after_cancellation < coupon_applied.min_purchase_amount:
                                # total_order_value_after_cancellation += order.coupon_amount
                                order.coupon_amount = Decimal(0)
                                logger.info("Coupon invalidated due to min purchase violation | new_total=%s | min_required=%s", total_order_value_after_cancellation, coupon_applied.min_purchase_amount)                                    
                            order.total_price = total_order_value_after_cancellation
                            order.save()

                        # Update the product variant quantity
                        if item.variants:
                            item.variants.qty += item.quantity
                            item.variants.save()
                            logger.debug("Stock restored | variant_id=%s | qty_added=%s", item.variants.variant_id, item.quantity)

                        # Change the item status to 'Cancelled'
                        item.status = 'Cancelled'
                        item.save()

                        if order.items.filter(status='Cancelled').count() == order.items.count():
                            full_refund_amount = order.total_price  

                            if full_refund_amount > 0:
                                user_wallet, created = Wallet.objects.get_or_create(user_id=user)
                                user_wallet.balance = Decimal(user_wallet.balance or 0) + full_refund_amount
                                user_wallet.save()

                                # Record the full refund transaction
                                details_text = f"Order Tax and Delivery charge"
                                Transaction.objects.create(
                                    wallet_id=user_wallet,
                                    transaction_type='Order cancellation',
                                    amount=full_refund_amount,
                                    details=details_text
                                )
                                logger.info("Final tax+delivery refund | order_id=%s | amount=%s", order.order_id)

                            order.total_price = Decimal(0)  
                            order.save()

                    elif order.payment_status == 'Pending':
                        if item.variants:
                            item.variants.qty += item.quantity
                            item.variants.save()
                            logger.debug("Stock restored (pending) | variant_id=%s", item.variants.variant_id)
                        
                        item.status = 'Cancelled'
                        item.save()
                    else:
                        logger.debug("Non-success payment status | current=%s", order.payment_status)
                        order.payment_status = 'Pending'
                        order.save()
                        if item.variants:
                            item.variants.qty += item.quantity
                            item.variants.save()
                        
                        item.status = 'Cancelled'
                        item.save()
                    # new
                        if order.items.count() > 1:
                            order.total_price -= item.subtotal_price  
                            order.save()

                if action == 'Delivered':
                    logger.info("Order marked as Delivered | orderitem_id=%s", order_id)
                    order.order.payment_status = 'Pending'
                    order.order.save()
                    logger.debug("Payment status set to Pending on delivery")
                
                if action == 'Approve Returned':
                    logger.info("Admin approved return | orderitem_id=%s", order_id)
                    item = order  # This is the OrderItem being processed
                    the_order = item.order
                    user = the_order.user

                    with transaction.atomic():
                        # Restock variant
                        if item.variants:
                            item.variants.qty += item.quantity
                            item.variants.save()

                        # Wallet
                        user_wallet, _ = Wallet.objects.get_or_create(user_id=user)
                        logger.debug("Wallet accessed for return | user_id=%s | balance=%s", user.userid, user_wallet.balance)

                        # Count remaining items (not cancelled / returned)
                        remaining_active_items = the_order.items.exclude(status__in=['Cancelled', 'Approve Returned'])
                        is_last_item = (remaining_active_items.count() == 1 and remaining_active_items.first().orderitem_id == item.orderitem_id)

                        # Safe values
                        old_total = Decimal(the_order.total_price or 0)
                        item_subtotal = Decimal(item.subtotal_price or 0)
                        order_coupon = Decimal(the_order.coupon_amount or 0)

                        if is_last_item:
                            # FULL REFUND
                            refund_amount = old_total

                            user_wallet.balance = Decimal(user_wallet.balance or 0) + refund_amount
                            user_wallet.save()

                            Transaction.objects.create(
                                wallet_id=user_wallet,
                                transaction_type='Full Return Refund',
                                amount=refund_amount,
                                details=f"Full return approved for order #{the_order.tracking_number}"
                            )
                            logger.info("Full return refund | order_id=%s | amount=%s", the_order.order_id, refund_amount)

                            the_order.total_price = Decimal('0.00')
                            the_order.coupon_amount = Decimal('0.00')
                            the_order.coupon_code = None
                            the_order.save()

                        else:
                            # PARTIAL REFUND BASED ON WHAT USER ACTUALLY PAID
                            # New total after removing item (but coupon stays applied)
                            new_total = old_total - item_subtotal

                            # Refund only difference in what user paid
                            refund_amount = old_total - new_total

                            user_wallet.balance = Decimal(user_wallet.balance or 0) + refund_amount
                            user_wallet.save()

                            Transaction.objects.create(
                                wallet_id=user_wallet,
                                transaction_type='Item Return Refund',
                                amount=refund_amount,
                                details=f"Return approved: {item.variants.product.product_name} (x{item.quantity})"
                            )
                            logger.info("Partial return refund | orderitem_id=%s | amount=%s", item.orderitem_id, refund_amount)
                            # Update order total
                            the_order.total_price = new_total
                            the_order.save()

                        # Mark item returned
                        item.status = 'Approve Returned'
                        item.save()

                        messages.success(request, f"Return approved. ₹{refund_amount} refunded to wallet.")

                order.save() 
                messages.success(request, f"Order status updated to {action}.")
                logger.info("Status update completed successfully | orderitem_id=%s | new_status=%s", order_id, action)
                return redirect('order:order_details') 
            else:
                logger.warning("Invalid status transition | from=%s | to=%s", current_status, action)
                messages.error(request, f"Invalid status transition from {current_status} to {action}.")

            return redirect('order:order_details')
    return render(request, 'admin/orders.html', {'orders': orders,'search_query':search_query}) 



def return_order(request, orderitem_id):
    logger.debug("return_order called | orderitem_id=%s", orderitem_id)
    item = get_object_or_404(OrderItem, orderitem_id=orderitem_id) 
    item.status = 'Requested Return'
    item.save()
    logger.info("Return requested | orderitem_id=%s", orderitem_id)
    messages.success(request, 'Your order has been returned successfully.')
    return redirect('order:view_orders')



@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff, login_url='accounts:admin_login')
def single_order(request,orderitem_id):
    logger.debug("single_order admin view | orderitem_id=%s", orderitem_id)
    order=OrderItem.objects.get(orderitem_id=orderitem_id)

    return render(request,'admin/single_order.html',{'order':order})


@never_cache
def download_invoice(request, orderitem_id):
    logger.debug("download_invoice called | orderitem_id=%s", orderitem_id)
    try:
        order_item = get_object_or_404(OrderItem, orderitem_id=orderitem_id)
        order = order_item.order
        all_order_items = OrderItem.objects.filter(order=order)

        html_content = render_to_string('user/invoice_template.html', {
            'order': order,
            'all_order_items': all_order_items
        })

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{order.tracking_number}.pdf"'

        try:
            pisa_status = pisa.CreatePDF(html_content, dest=response)
            if pisa_status.err:
                logger.error("PDF generation failed | order_id=%s", order.order_id)
                return HttpResponse('Error generating PDF', status=500)
            logger.info("Invoice PDF generated | order_id=%s", order.order_id)
        except Exception as e:
            logger.error("PDF generation error | error=%s", e)
            return HttpResponse('Error generating PDF', status=500)

        return response

    except OrderItem.DoesNotExist:
        logger.warning("Order item not found for invoice | orderitem_id=%s", orderitem_id)
        messages.error(request, 'Order item not found.')
        return redirect('order:view_orders')
    except Exception as e:
        logger.error("Unexpected error in download_invoice | error=%s", e)
        messages.error(request, 'An unexpected error occurred while generating the invoice.')
        return redirect('order:view_orders')