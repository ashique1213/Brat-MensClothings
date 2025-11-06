from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.models import Users
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache
from django.db.models import Q
import re
from django.http import JsonResponse
from decimal import Decimal
from .models import Product_Offers, Brand_Offers
from products.models import ProductDetails, Brand
import logging
logger = logging.getLogger('offer.views')


def is_staff(user):
    return user.is_staff


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff, 'accounts:admin_login')
def view_offer(request):
    logger.debug("view_offer called | user=%s", request.user)
    return render(request, 'admin/offer/offers.html')


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff, 'accounts:admin_login')
def view_product_offer(request):
    logger.debug("view_product_offer called | method=%s | user=%s", request.method, request.user)

    search_query = request.GET.get('search', '')

    if search_query:
        product_offer = Product_Offers.objects.filter(
            Q(offer_name__icontains=search_query) | Q(product__product_name__icontains=search_query)
        )
        logger.info("Product offer search: '%s' | results=%d", search_query, product_offer.count())
    else:
        product_offer = Product_Offers.objects.all()
        logger.debug("All product offers loaded | count=%d", product_offer.count())

    products = ProductDetails.objects.all()
    return render(request, 'admin/offer/product_offer.html', {
        'products': products,
        'product_offer': product_offer,
        'search_query': search_query
    })


def add_product_offer(request):
    logger.debug("add_product_offer called | method=%s | user=%s", request.method, request.user)

    if request.method == "POST":
        offer_name = request.POST.get("offer_name", "").strip()
        product_id = request.POST.get("product_id")
        offer_price = request.POST.get("offer_price", "")
        offer_details = request.POST.get("offer_details", "")
        started_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

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
            offer_price_decimal = Decimal(offer_price)
            if offer_price_decimal <= 0:
                errors['offer_price'] = 'Offer price must be greater than 0.'
            elif offer_price_decimal > product_price * Decimal('0.1'):
                errors['offer_price'] = 'Offer price must be at least 10% of the product price.'
        except (ValueError, ProductDetails.DoesNotExist):
            errors['offer_price'] = 'Invalid offer price or product.'

        if not started_date or not end_date:
            errors['dates'] = 'Invalid date format.'
        elif started_date >= end_date:
            errors['dates'] = 'End date must be after the start date.'

        if errors:
            logger.warning("Product offer creation failed | offer_name=%s | errors=%s", offer_name, errors)
            return JsonResponse({'success': False, 'errors': errors})

        try:
            product = ProductDetails.objects.get(product_id=product_id)
            new_offer = Product_Offers(
                offer_name=offer_name,
                product_id=product_id,
                offer_price=offer_price_decimal,
                offer_details=offer_details,
                started_date=started_date,
                end_date=end_date,
                status=True
            )
            new_offer.save()
            logger.info("Product offer added | offer_name=%s | product_id=%s | offer_price=%s", offer_name, product_id, offer_price_decimal)
            return JsonResponse({'success': True, 'message': 'Offer Updated successfully!'})
        except Exception as e:
            logger.error("Error creating product offer | offer_name=%s | error=%s", offer_name, e, exc_info=True)
            return JsonResponse({'success': False, 'errors': {'server': 'Failed to create offer.'}})

    products = ProductDetails.objects.all()
    return render(request, 'admin/offer/product_offer.html', {'products': products})



def edit_product_offer(request, offer_id):
    logger.debug("edit_product_offer called | offer_id=%s | method=%s", offer_id, request.method)

    offer = get_object_or_404(Product_Offers, id=offer_id)

    if request.method == "POST":
        offer_name = request.POST.get("offer_name", "").strip()
        product_id = request.POST.get("product_id")
        offer_price = request.POST.get("offer_price", "")
        offer_details = request.POST.get("offer_details", "")
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
            offer_price_decimal = Decimal(offer_price)
            if offer_price_decimal <= 0:
                errors['offer_price'] = 'Offer price must be greater than 0.'
            elif offer_price_decimal > product_price * Decimal('0.1'):
                errors['offer_price'] = 'Offer price must be at least 10% of the product price.'
        except (ValueError, ProductDetails.DoesNotExist):
            errors['offer_price'] = 'Invalid offer price or product.'

        if not start_date or not end_date:
            errors['dates'] = 'Invalid date format.'
        elif start_date >= end_date:
            errors['dates'] = 'End date must be after the start date.'

        if errors:
            logger.warning("Product offer edit failed | offer_id=%s | errors=%s", offer_id, errors)
            return JsonResponse({'success': False, 'errors': errors})

        try:
            offer.offer_name = offer_name
            offer.product_id = product_id
            offer.offer_price = offer_price_decimal
            offer.offer_details = offer_details
            offer.started_date = start_date
            offer.end_date = end_date
            offer.save()
            logger.info("Product offer updated | offer_id=%s | offer_name=%s", offer_id, offer_name)
            return JsonResponse({'success': True, 'message': 'Offer updated successfully!'})
        except Exception as e:
            logger.error("Error updating product offer | offer_id=%s | error=%s", offer_id, e, exc_info=True)
            return JsonResponse({'success': False, 'errors': {'server': 'Update failed.'}})

    products = ProductDetails.objects.all()
    return render(request, 'admin/offer/product_offer.html', {'products': products, 'offer': offer})



@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff, 'accounts:admin_login')
def view_brand_offer(request):
    logger.debug("view_brand_offer called | method=%s | user=%s", request.method, request.user)

    search_query = request.GET.get('search', '')

    if search_query:
        brand_offers = Brand_Offers.objects.filter(
            Q(offer_name__icontains=search_query) | Q(brand__brandname__icontains=search_query)
        )
        logger.info("Brand offer search: '%s' | results=%d", search_query, brand_offers.count())
    else:
        brand_offers = Brand_Offers.objects.all()
        logger.debug("All brand offers loaded | count=%d", brand_offers.count())

    brands = Brand.objects.all()
    return render(request, 'admin/offer/brand_offer.html', {
        'brands': brands,
        'brand_offers': brand_offers,
        'search_query': search_query
    })


def add_brand_offer(request):
    logger.debug("add_brand_offer called | method=%s | user=%s", request.method, request.user)

    if request.method == "POST":
        offer_name = request.POST.get("offer_name", "").strip()
        brand_id = request.POST.get("brand_id")
        offer_price = request.POST.get("offer_price", "")
        offer_details = request.POST.get("offer_details", "")
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
            offer_price_decimal = Decimal(offer_price)
            if offer_price_decimal <= 0:
                errors['offer_price'] = 'Offer price must be greater than 0.'
            elif offer_price_decimal >= 150:
                errors['offer_price'] = 'Offer price must be less than 150.'
        except ValueError:
            errors['offer_price'] = 'Invalid offer price.'

        if not started_date or not end_date:
            errors['dates'] = 'Start date and end date are required.'
        elif started_date >= end_date:
            errors['dates'] = 'End date must be after the start date.'

        if errors:
            logger.warning("Brand offer creation failed | offer_name=%s | brand_id=%s | errors=%s", offer_name, brand_id, errors)
            return JsonResponse({'success': False, 'errors': errors})

        try:
            brand = Brand.objects.get(brand_id=brand_id)
            new_offer = Brand_Offers(
                offer_name=offer_name,
                brand_id=brand_id,
                offer_price=offer_price_decimal,
                offer_details=offer_details,
                started_date=started_date,
                end_date=end_date,
                status=True
            )
            new_offer.save()
            logger.info("Brand offer added | offer_name=%s | brand_id=%s | offer_price=%s", offer_name, brand_id, offer_price_decimal)
            return JsonResponse({'success': True, 'message': 'Offer added successfully!'})
        except Exception as e:
            logger.error("Error creating brand offer | offer_name=%s | error=%s", offer_name, e, exc_info=True)
            return JsonResponse({'success': False, 'errors': {'server': 'Failed to create offer.'}})

    brands = Brand.objects.all()
    return render(request, 'admin/offer/brand_offer.html', {'brands': brands})


def edit_brand_offer(request, offer_id):
    logger.debug("edit_brand_offer called | offer_id=%s | method=%s", offer_id, request.method)

    offer = get_object_or_404(Brand_Offers, id=offer_id)

    if request.method == "POST":
        offer_name = request.POST.get("offer_name", "").strip()
        brand_id = request.POST.get("brand_id")
        offer_price = request.POST.get("offer_price", "")
        offer_details = request.POST.get("offer_details", "")
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
            offer_price_decimal = Decimal(offer_price)
            if offer_price_decimal <= 0:
                errors['offer_price'] = 'Offer price must be greater than 0.'
            elif offer_price_decimal >= 150:
                errors['offer_price'] = 'Offer price must be less than 150.'
        except ValueError:
            errors['offer_price'] = 'Invalid offer price.'

        if not start_date or not end_date:
            errors['dates'] = 'Start date and end date are required.'
        elif start_date >= end_date:
            errors['dates'] = 'End date must be after the start date.'

        if errors:
            logger.warning("Brand offer edit failed | offer_id=%s | errors=%s", offer_id, errors)
            return JsonResponse({'success': False, 'errors': errors})

        try:
            brand = Brand.objects.get(brand_id=brand_id)
            offer.offer_name = offer_name
            offer.brand_id = brand_id
            offer.offer_price = offer_price_decimal
            offer.offer_details = offer_details
            offer.started_date = start_date
            offer.end_date = end_date
            offer.status = True
            offer.save()
            logger.info("Brand offer updated | offer_id=%s | offer_name=%s", offer_id, offer_name)
            return JsonResponse({'success': True, 'message': 'Offer updated successfully!'})
        except Exception as e:
            logger.error("Error updating brand offer | offer_id=%s | error=%s", offer_id, e, exc_info=True)
            return JsonResponse({'success': False, 'errors': {'server': 'Update failed.'}})

    brands = Brand.objects.all()
    return render(request, 'admin/offer/brand_offer_edit.html', {'offer': offer, 'brands': brands})