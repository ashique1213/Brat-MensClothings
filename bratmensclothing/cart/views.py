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
from decimal import Decimal


@never_cache
def view_cart(request):
    cart_items = []
    grand_total = Decimal('0.0')
    tax = Decimal('0.0')
    delivery_charge = Decimal('50.0')

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        cart_items = cart.items.all() if cart else []  

        total = sum(items.item_total for items in cart_items)
        tax_rate = Decimal('0.02')
        tax = total * tax_rate
        grand_total = total + tax + delivery_charge

    else:
        cart_items = []

    return render(request, 'user/cart.html', {
        'cart_items': cart_items,
        'grand_total':grand_total,
        'tax':tax,
        'cart':cart if request.user.is_authenticated else None,
        'delivery_charge':delivery_charge,
        })


@never_cache
def add_to_cart(request, variant_id):
    if request.user.is_authenticated:
        variant = get_object_or_404(VariantSize, variant_id=variant_id)
        quantity = int(request.POST.get('quantity', 1))

        if variant.qty==0:
            messages.error(request, "The product is out of stock")
            return redirect('userss:product_details',product_id=variant.product.product_id)
        
        if quantity>variant.qty:
            messages.error(request, "You have selected a quantity above the available stock.")
            return redirect('userss:product_details',product_id=variant.product.product_id)

        cart, created = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, variant=variant)
        # cart_item.quantity += quantity if not created else quantity
        # cart_item.save()

        if cart_item.quantity + quantity > 6:
            cart_item.quantity = 6  
            messages.error(request, "You already have 6 in your cart")
            return redirect('userss:product_details',product_id=variant.product.product_id)
        else:
            cart_item.quantity += quantity
            cart_item.save()

        messages.success(request, "Item added to cart succesfully")
    else:
        messages.error(request, "Please log in to add items to your cart.")

    return redirect('cart:viewcart')


def delete_item(request,cartitem_id):
    item=get_object_or_404(CartItem,cartitem_id=cartitem_id)

    item.delete()
    messages.success(request, "Item deleted successfully ")
    return redirect('cart:viewcart')

@require_POST
def update_cart_item(request, cart_item_id):
    data = json.loads(request.body)
    quantity = data.get('quantity')

    try:
        cart_item = CartItem.objects.get(cartitem_id=cart_item_id)
        cart_item.quantity = quantity
        cart_item.save()

        return JsonResponse({
            'success': True,
            'new_total': cart_item.item_total  # Calculate the new total based on updated quantity
        })
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)