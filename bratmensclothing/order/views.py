from django.shortcuts import render,redirect,get_object_or_404
from accounts.models import Users
from products.models import ProductDetails,Category,Brand,VariantSize
from cart.models import Cart, CartItem
from users.models import Address
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import never_cache
from django.db.models import Q
import re
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


@never_cache
def checkout(request):
    if request.user.is_authenticated:
        user=request.user
        addresses=Address.objects.filter(user=user)
        cart=get_object_or_404(Cart,user=user)
        cart_items=CartItem.objects.filter(cart=cart)

        total_quantity=sum(items.quantity for items in cart_items )
        if total_quantity > 10:
            messages.error(request, 'You have exceeded the limit of 10 items in your cart!!')
            return redirect('cart:viewcart')

        total = sum(items.item_total for items in cart_items)
        tax_rate = 0.02
        tax = total * tax_rate
        grand_total = total + tax + 50
        
    return render(request,'user/checkout.html',
                {
                    'user':user,
                    'addresses':addresses,
                    'cart_items':cart_items,
                    'tax':tax,
                    'grand_total':grand_total

                }) 

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