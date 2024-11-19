from django.shortcuts import render,redirect,get_object_or_404
from accounts.models import Users
from products.models import ProductDetails,Brand
from users.models import Address
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import never_cache
from django.db.models import Q
import re
from django.http import JsonResponse
from decimal import Decimal
from .models import Product_Offers,Brand_Offers

def is_staff(user):
    return user.is_staff

@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff,'accounts:admin_login')
def view_offer(request):

    return render(request,'admin/offer/offers.html')


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff,'accounts:admin_login')
def view_product_offer(request):

    search_query=request.GET.get('search','') 

    if search_query:
        product_offer=Product_Offers.objects.filter(
            Q(offer_name__icontains=search_query) | Q(product__product_name__icontains=search_query)
        )
    else:
        product_offer=Product_Offers.objects.all()

    products = ProductDetails.objects.all()
    return render(request,'admin/offer/product_offer.html',{'products':products,'product_offer':product_offer,'search_query':search_query})

def add_product_offer(request):
    if request.method == "POST":
        offer_name = request.POST.get("offer_name").strip()
        product_id = request.POST.get("product_id")
        offer_price = request.POST.get("offer_price")
        offer_details = request.POST.get("offer_details")
        started_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        print(f'{started_date}')
        print(f'{end_date}')

        errors = {}

        if not offer_name:
            errors['offer_name'] = 'Offer name can\'t be empty.'
        elif Product_Offers.objects.filter(offer_name=offer_name).exists():
            errors['offer_name'] = 'Offer name already exists.'

        if Product_Offers.objects.filter(product_id=product_id).exists():
            errors['product_name_error'] = 'Product already has an existing offer.'

        try:
            product = ProductDetails.objects.get(product_id=product_id)

            product_price = product.price 

            offer_price = Decimal(offer_price)
            if offer_price <= 0:
                errors['offer_price'] = 'Offer price must be greater than 0.'
            elif offer_price > product_price * Decimal (0.1):  
                errors['offer_price'] = 'Offer price must be at least 10% of the product price.'
        except ValueError:
            errors['offer_price'] = 'Invalid offer price.'

        if not started_date or not end_date:
            errors['dates'] = 'Invalid date format.'
        elif started_date >= end_date:
            errors['dates'] = 'End date must be after the start date.'

        if errors:
            return JsonResponse({'success': False, 'errors': errors})
        
        if offer_name and product_id and offer_price and started_date and end_date:
            try:
                product = ProductDetails.objects.get(product_id=product_id)
                new_offer = Product_Offers(
                    offer_name=offer_name,
                    product_id=product_id,
                    offer_price=offer_price,
                    offer_details=offer_details,
                    started_date=started_date,
                    end_date=end_date,
                    status=True  
                )
                print(f'{started_date}')
                print(f'{end_date}')
                new_offer.save()
                # messages.success(request, 'Offer added successfully!')
                # return redirect('offer:view_product_offer')  
                return JsonResponse({'success': True, 'message': 'Offer Updated successfully!'})

            except ProductDetails.DoesNotExist:
                messages.error(request, 'Product not found.')
        else:
            messages.error(request, 'All fields are required.')
            

    products = ProductDetails.objects.all()
    return render(request, 'admin/offer/product_offer.html', {'products': products})



def edit_product_offer(request, offer_id):
    offer = get_object_or_404(Product_Offers, id=offer_id)
    
    if request.method == "POST":
        offer_name = request.POST.get("offer_name").strip()
        product_id = request.POST.get("product_id")
        offer_price = request.POST.get("offer_price")
        offer_details = request.POST.get("offer_details")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        errors = {}

        if not offer_name:
            errors['offer_name'] = 'Offer name can\'t be empty.'
        elif Product_Offers.objects.filter(offer_name=offer_name).exclude(id=offer_id).exists():
            errors['offer_name'] = 'Offer name already exists.'

        if Product_Offers.objects.filter(product_id=product_id).exclude(id=offer_id).exists():
            errors['product_name_error'] = 'Product already has an existing offer.'

        try:
            product = ProductDetails.objects.get(product_id=product_id)
            product_price = product.price 

            offer_price = Decimal(offer_price)
            if offer_price <= 0:
                errors['offer_price'] = 'Offer price must be greater than 0.'
            elif offer_price > product_price * Decimal (0.1):  
                errors['offer_price'] = 'Offer price must be at least 10% of the product price.'
        except ValueError:
            errors['offer_price'] = 'Invalid offer price.'

        if not start_date or not end_date:
            errors['dates'] = 'Invalid date format.'
        elif start_date >= end_date:
            errors['dates'] = 'End date must be after the start date.'

        if errors:
            return JsonResponse({'success': False, 'errors': errors})
        
        if offer_name and product_id and offer_price and start_date and end_date:
            try:
                product = ProductDetails.objects.get(product_id=product_id)
                offer.offer_name = offer_name
                offer.product_id = product_id
                offer.offer_price = offer_price
                offer.offer_details = offer_details
                offer.started_date = start_date
                offer.end_date = end_date
                offer.save()
                return JsonResponse({'success': True, 'message': 'Offer updated successfully!'})

            except ProductDetails.DoesNotExist:
                errors['product_name_error'] = 'Product not found.'
                return JsonResponse({'success': False, 'errors': errors})

    products = ProductDetails.objects.all()
    return render(request, 'admin/offer/product_offer.html', {'products': products, 'offer': offer})



@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff,'accounts:admin_login')
def view_brand_offer(request):
    search_query=request.GET.get('search','') 

    if search_query:
        brand_offers=Brand_Offers.objects.filter(
            Q(offer_name__icontains=search_query) | Q(brand__brandname__icontains=search_query)
        )
    else:
        brand_offers=Brand_Offers.objects.all()
    brands = Brand.objects.all()
    return render(request,'admin/offer/brand_offer.html', {'brands': brands,'brand_offers':brand_offers,'search_query':search_query})


def add_brand_offer(request):
    if request.method == "POST":
        offer_name = request.POST.get("offer_name").strip()
        brand_id = request.POST.get("brand_id")
        offer_price = request.POST.get("offer_price")
        offer_details = request.POST.get("offer_details")
        started_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")


        errors = {}

        if not offer_name:
            errors['offer_name'] = 'Offer name can\'t be empty.'
        elif Brand_Offers.objects.filter(offer_name=offer_name).exists():
            errors['offer_name'] = 'Offer name Exists'  

        if not brand_id:
            errors['brand_id'] = 'Brand is required.'
        elif Brand_Offers.objects.filter(brand_id=brand_id).exists():
            errors['brand_id'] = 'Brand name Exists'


        if not offer_price:
            errors['offer_price'] = 'Offer price is required.'

        try:
            offer_price = Decimal(offer_price) 
            if offer_price <= 0:
                errors['offer_price'] = 'Offer price must be greater than 0.'
            elif offer_price >= 150:
                errors['offer_price'] = 'Offer price must be less than 150.'
        except ValueError:
            errors['offer_price'] = 'Invalid offer price.'

        if not started_date or not end_date:
            errors['dates'] = 'Start date and end date are required.'
        elif started_date >= end_date:
            errors['dates'] = 'End date must be after the start date.'
        
        if errors:
            return JsonResponse({'success': False, 'errors': errors})
        
        if offer_name and brand_id and offer_price and started_date and end_date:
            try:
                brand = Brand.objects.get(brand_id=brand_id)
                new_offer = Brand_Offers(
                    offer_name=offer_name,
                    brand_id=brand_id,
                    offer_price=offer_price,
                    offer_details=offer_details,
                    started_date=started_date,
                    end_date=end_date,
                    status=True  
                )
                new_offer.save()
                # messages.success(request, 'Offer added successfully!')
                # return redirect('offer:view_brand_offer')  
                return JsonResponse({'success': True, 'message': 'Offer added successfully!'})
            except Brand.DoesNotExist:
                messages.error(request, 'Product not found.')
        else:
            messages.error(request, 'All fields are required.')

    brands = Brand.objects.all()
    return render(request, 'admin/offer/brand_offer.html', {'brands': brands})


def edit_brand_offer(request, offer_id):
    offer = get_object_or_404(Brand_Offers, id=offer_id)

    if request.method == "POST":
        offer_name = request.POST.get("offer_name").strip()
        brand_id = request.POST.get("brand_id")
        offer_price = request.POST.get("offer_price")
        offer_details = request.POST.get("offer_details")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        errors = {}

        if not offer_name:
            errors['offer_name'] = 'Offer name can\'t be empty.'
        elif Brand_Offers.objects.filter(offer_name=offer_name).exclude(id=offer_id).exists():
            errors['offer_name'] = 'Offer name Exists'  

        if not brand_id:
            errors['brand_id'] = 'Brand is required.'
        elif Brand_Offers.objects.filter(brand_id=brand_id).exclude(id=offer_id).exists():
            errors['brand_id'] = 'Brand name Exists'


        if not offer_price:
            errors['offer_price'] = 'Offer price is required.'

        try:
            offer_price = Decimal(offer_price) 
            if offer_price <= 0:
                errors['offer_price'] = 'Offer price must be greater than 0.'
            elif offer_price >= 150:
                errors['offer_price'] = 'Offer price must be less than 150.'
        except ValueError:
            errors['offer_price'] = 'Invalid offer price.'

        if not start_date or not end_date:
            errors['dates'] = 'Start date and end date are required.'
        elif start_date >= end_date:
            errors['dates'] = 'End date must be after the start date.'
        
        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        if offer_name and brand_id and offer_price and start_date and end_date:
            try:
                brand = Brand.objects.get(brand_id=brand_id)
                # Update the offer details
                offer.offer_name = offer_name
                offer.brand_id = brand
                offer.offer_price = offer_price
                offer.offer_details = offer_details
                offer.started_date = start_date
                offer.end_date = end_date
                offer.status = True 
                offer.save()

                # messages.success(request, 'Offer updated successfully!')
                # return redirect('offer:view_brand_offer') 
                return JsonResponse({'success': True, 'message': 'Offer updated successfully!'})

            except Brand.DoesNotExist:
                messages.error(request, 'Brand not found.')
        else:
            messages.error(request, 'All fields are required.')

    brands = Brand.objects.all()
    return render(request, 'admin/offer/brand_offer_edit.html', {'offer': offer, 'brands': brands})
