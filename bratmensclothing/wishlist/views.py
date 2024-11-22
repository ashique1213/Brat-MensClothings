from django.shortcuts import render,redirect,get_object_or_404
from accounts.models import Users
from products.models import ProductDetails,Category,Brand,VariantSize
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from .models import Wishlist

@never_cache
def view_wishlist(request):
    if request.user.is_authenticated:
        Wishlist_items=Wishlist.objects.filter(user=request.user)
    else:
        Wishlist_items = []
    return render(request,'user/wishlist.html',{'Wishlist_items':Wishlist_items})
    
    # messages.error(request,'Please sign in')
    # return render(request,'user/login.html')


def add_to_wishlist(request, product_id):
    if request.user.is_authenticated:
        variants = VariantSize.objects.filter(product__product_id=product_id)

        variant = variants.first()  
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=variant)

        if created:
            messages.success(request, "Item added to your wishlist!")
        else:
            messages.info(request, "Item already in your wishlist.")

        return redirect('userss:category_details')
    else:
        messages.error(request, "You need to be logged in.")
        return redirect('userss:login')


def remove_wishlist(request,variant_id):
    product=Wishlist.objects.filter(product_id=variant_id)

    product.delete()
    messages.success(request, "Item removed to your wishlist!")
    return redirect('wishlist:viewwishlist')


def clear_wishlist(request):
    if request.user.is_authenticated:
        Wishlist.objects.filter(user=request.user).delete()
        
        messages.success(request, "Your wishlist has been cleared!")
    else:
        messages.error(request, "You need to be logged in.")
    
    return redirect('wishlist:viewwishlist')
