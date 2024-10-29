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


@never_cache
def view_cart(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        cart_items = cart.items.all() if cart else []  
    else:
        cart_items = []

    return render(request, 'user/cart.html', {'cart_items': cart_items})


@never_cache
def add_to_cart(request, variant_id):
    if request.user.is_authenticated:
        variant = get_object_or_404(VariantSize, variant_id=variant_id)
        quantity = int(request.POST.get('quantity', 1))

        cart, created = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, variant=variant)
        cart_item.quantity += quantity if not created else quantity
        cart_item.save()

        messages.success(request, "Item added to cart!")
    else:
        messages.error(request, "Please log in to add items to your cart.")

    return redirect('cart:viewcart')


def delete_item(request,cartitem_id):
    item=get_object_or_404(CartItem,cartitem_id=cartitem_id)

    item.delete()
    messages.success(request, "Item deleted successfully ")
    return redirect('cart:viewcart')