from django.shortcuts import render, redirect, get_object_or_404
from .models import Brand, Category, ProductDetails, VariantSize, Review
from accounts.models import Users
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache
from django.db.models import F
from django.http import JsonResponse
from decimal import Decimal
from django.core.paginator import Paginator
from django.db.models import Q
import logging
logger = logging.getLogger('products.views')


def is_staff(user):
    return user.is_staff


def add_brands(request):
    logger.debug("add_brands called | method=%s | user=%s", request.method, request.user)

    if request.method == 'POST':
        brand = request.POST.get('brandname', '').strip()
        errors = {}

        if not brand:
            errors['brand_error'] = 'Brand name is required.'
        elif len(brand) < 2:
            errors['brand_error'] = 'Brand name must be at least 2 characters long.'
        elif Brand.objects.filter(brandname__iexact=brand).exists():
            errors['brand_error'] = 'Brand already exists.'

        if errors:
            logger.warning("Brand creation failed | brand=%s | errors=%s", brand, errors)
            return JsonResponse({'success': False, 'errors': errors})

        try:
            Brand.objects.create(brandname=brand)
            logger.info("Brand added | brandname=%s", brand)
            return JsonResponse({'success': True, 'message': 'Brand added successfully!'})
        except Exception as e:
            logger.error("Error creating brand | brand=%s | error=%s", brand, e, exc_info=True)
            return JsonResponse({'success': False, 'errors': {'server': 'Failed to add brand.'}})

    return render(request, 'admin/brand.html')


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff, 'accounts:admin_login')
def view_brands(request):
    logger.debug("view_brands called | user=%s", request.user)

    search_query = request.GET.get('search', '')

    if search_query:
        brands = Brand.objects.filter(
            brandname__icontains=search_query
        ).order_by('is_deleted', '-created_at')
        logger.info("Brand search | query='%s' | results=%d", search_query, brands.count())
    else:
        brands = Brand.objects.all().order_by('is_deleted', '-created_at')
        logger.debug("All brands loaded | count=%d", brands.count())

    paginator = Paginator(brands, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/brand.html', {
        'brands': page_obj,
        'search_query': search_query
    })


def edit_brands(request, brand_id):
    logger.debug("edit_brands called | brand_id=%s | method=%s", brand_id, request.method)

    brand = get_object_or_404(Brand, brand_id=brand_id)

    if request.method == 'POST':
        brandname = request.POST.get('brandname', '').strip()
        errors = {}

        if not brandname:
            errors['brand_error'] = 'Brand name is required.'
        elif len(brandname) < 2:
            errors['brand_error'] = 'Brand name must be at least 2 characters long.'
        elif Brand.objects.filter(brandname__iexact=brandname).exclude(brand_id=brand_id).exists():
            errors['brand_error'] = 'Brand already exists.'

        if errors:
            logger.warning("Brand edit failed | brand_id=%s | errors=%s", brand_id, errors)
            return JsonResponse({'success': False, 'errors': errors})

        try:
            brand.brandname = brandname
            brand.save()
            logger.info("Brand updated | brand_id=%s | new_name=%s", brand_id, brandname)
            return JsonResponse({'success': True, 'message': 'Brand updated successfully!'})
        except Exception as e:
            logger.error("Error updating brand | brand_id=%s | error=%s", brand_id, e, exc_info=True)
            return JsonResponse({'success': False, 'errors': {'server': 'Update failed.'}})

    return render(request, 'admin/brand.html', {'brand': brand})


def soft_delete_brand(request, brand_id):
    logger.debug("soft_delete_brand called | brand_id=%s", brand_id)
    brand = get_object_or_404(Brand, brand_id=brand_id)
    brand.is_deleted = True
    brand.save()
    logger.info("Brand soft-deleted | brand_id=%s | name=%s", brand_id, brand.brandname)
    messages.success(request, 'Brand successfully Unlisted!')
    return redirect('products:view_brands')


def restore_brand(request, brand_id):
    logger.debug("restore_brand called | brand_id=%s", brand_id)
    brand = get_object_or_404(Brand, brand_id=brand_id)
    brand.is_deleted = False
    brand.save()
    logger.info("Brand restored | brand_id=%s | name=%s", brand_id, brand.brandname)
    messages.success(request, 'Brand successfully listed!')
    return redirect('products:view_brands')


def add_category(request):
    logger.debug("add_category called | method=%s", request.method)

    if request.method == 'POST':
        category = request.POST.get('category')
        categorytype = request.POST.get('categorytype')

        try:
            Category.objects.create(category=category, category_type=categorytype)
            logger.info("Category added | name=%s | type=%s", category, categorytype)
            messages.success(request, 'Category added successfully!')
            return redirect('products:view_category')
        except Exception as e:
            logger.error("Error adding category | name=%s | error=%s", category, e, exc_info=True)
            messages.error(request, 'Failed to add category.')
            return redirect('products:view_category')

    return render(request, 'admin/category.html')


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff, 'accounts:admin_login')
def view_category(request):
    logger.debug("view_category called | user=%s", request.user)
    categories = Category.objects.all().order_by('is_deleted', '-created_date')
    logger.debug("All categories loaded | count=%d", categories.count())
    return render(request, 'admin/category.html', {'category': categories})


def soft_delete_category(request, category_id):
    logger.debug("soft_delete_category called | category_id=%s", category_id)
    category = get_object_or_404(Category, category_id=category_id)
    category.is_deleted = True
    category.save()
    logger.info("Category soft-deleted | category_id=%s | name=%s", category_id, category.category)
    messages.success(request, 'Category successfully Unlisted!')
    return redirect('products:view_category')


def restore_category(request, category_id):
    logger.debug("restore_category called | category_id=%s", category_id)
    category = get_object_or_404(Category, category_id=category_id)
    category.is_deleted = False
    category.save()
    logger.info("Category restored | category_id=%s | name=%s", category_id, category.category)
    messages.success(request, 'Category successfully listed!')
    return redirect('products:view_category')


def edit_category(request, category_id):
    logger.debug("edit_category called | category_id=%s | method=%s", category_id, request.method)

    category = get_object_or_404(Category, category_id=category_id)

    if request.method == 'POST':
        category_name = request.POST.get('category')
        category_type = request.POST.get('categorytype')
        category.category = category_name
        category.category_type = category_type
        category.save()
        logger.info("Category updated | category_id=%s | new_name=%s", category_id, category_name)
        messages.success(request, 'Category updated successfully!')
        return redirect('products:view_category')

    return render(request, 'admin/category.html', {'category': category})


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff, 'accounts:admin_login')
def viewproducts(request):
    logger.debug("viewproducts called | user=%s", request.user)

    search_query = request.GET.get('search', '')

    if search_query:
        products = ProductDetails.objects.filter(
            Q(product_name__icontains=search_query) |
            Q(category__category__icontains=search_query) |
            Q(brand__brandname__icontains=search_query)
        ).order_by('-created_at')
        logger.info("Product search | query='%s' | results=%d", search_query, products.count())
    else:
        products = ProductDetails.objects.all().order_by('-created_at')
        logger.debug("All products loaded | count=%d", products.count())

    brands = Brand.objects.filter(is_deleted=False)
    categories = Category.objects.filter(is_deleted=False)

    paginator = Paginator(products, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/products/product.html', {
        'products': page_obj,
        'brands': brands,
        'categories': categories,
        'search_query': search_query
    })


def addproducts(request):
    logger.debug("addproducts called | method=%s", request.method)

    if request.method == 'POST':
        productname = request.POST.get('productname', '').strip()
        description = request.POST.get('description', '').strip()
        brand_name = request.POST.get('brandname')
        category_ids = request.POST.getlist('category')
        price = request.POST.get('price', '0')
        color = request.POST.get('color', '').strip()
        occasion = request.POST.get('occasion')
        fit = request.POST.get('fit')
        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')
        image3 = request.FILES.get('image3')
        image4 = request.FILES.get('image4')

        errors = {}

        if not productname:
            errors['productname'] = 'Product name is required and cannot contain spaces.'
        elif ProductDetails.objects.filter(product_name__iexact=productname).exists():
            errors['productname'] = 'Product name already exists.'

        if not description:
            errors['description'] = 'Description is required.'
        elif len(description) < 10:
            errors['description'] = 'Description must be between 10 and 20 characters.'

        try:
            price_decimal = Decimal(price)
            if price_decimal < 400:
                errors['price'] = 'Price must be a number greater than or equal to 400.'
        except:
            errors['price'] = 'Price must be a valid number.'

        if not color:
            errors['color'] = 'Color is required and cannot be empty.'
        elif ' ' in color:
            errors['color'] = 'Color cannot contain spaces.'

        if errors:
            logger.warning("Product creation failed | name=%s | errors=%s", productname, errors)
            return JsonResponse({'success': False, 'errors': errors})

        try:
            brand = Brand.objects.get(brandname=brand_name)
            product = ProductDetails.objects.create(
                product_name=productname,
                description=description,
                brand=brand,
                price=price_decimal,
                color=color,
                occasion=occasion,
                fit=fit,
                image1=image1,
                image2=image2,
                image3=image3,
                image4=image4
            )
            product.category.set(category_ids)
            logger.info("Product added | product_id=%s | name=%s", product.product_id, productname)
            return JsonResponse({'success': True, 'message': 'Product added successfully!'})
        except Exception as e:
            logger.error("Error creating product | name=%s | error=%s", productname, e, exc_info=True)
            return JsonResponse({'success': False, 'errors': {'server': 'Failed to add product.'}})

    categories = Category.objects.filter(is_deleted=False)
    brands = Brand.objects.filter(is_deleted=False)
    return render(request, 'admin/products/product.html', {'categories': categories, 'brands': brands})


def editproduct(request, product_id):
    logger.debug("editproduct called | product_id=%s | method=%s", product_id, request.method)

    product = get_object_or_404(ProductDetails, product_id=product_id)
    brands = Brand.objects.filter(is_deleted=False)
    categories = Category.objects.filter(is_deleted=False)

    if request.method == 'POST':
        errors = {}

        product.product_name = request.POST.get('product_name', '').strip()
        if not product.product_name:
            errors['productname'] = 'Product name is required and cannot contain spaces.'
        elif ProductDetails.objects.filter(product_name__iexact=product.product_name).exclude(product_id=product_id).exists():
            errors['productname'] = 'Product name already exists.'

        product.description = request.POST.get('description', '').strip()
        if not product.description:
            errors['description'] = 'Description is required.'
        elif len(product.description) < 10:
            errors['description'] = 'Description must be between 10 and 500 characters.'

        brand_id = request.POST.get('brandname')
        if brand_id:
            product.brand_id = brand_id

        category_ids = request.POST.getlist('category')
        product.category.set(category_ids)

        product.color = request.POST.get('color', '').strip()
        product.price = request.POST.get('price')
        product.occasion = request.POST.get('occasion')
        product.fit = request.POST.get('fit')

        try:
            product.price = Decimal(product.price)
            if product.price < 400:
                errors['price'] = 'Price must be a number greater than or equal to 400.'
        except:
            errors['price'] = 'Price must be a valid number.'

        if not product.color:
            errors['color'] = 'Color is required and cannot be empty.'
        elif ' ' in product.color:
            errors['color'] = 'Color cannot contain spaces.'

        if errors:
            logger.warning("Product edit failed | product_id=%s | errors=%s", product_id, errors)
            return JsonResponse({'success': False, 'errors': errors})

        if 'image1' in request.FILES:
            product.image1 = request.FILES['image1']
        if 'image2' in request.FILES:
            product.image2 = request.FILES['image2']
        if 'image3' in request.FILES:
            product.image3 = request.FILES['image3']
        if 'image4' in request.FILES:
            product.image4 = request.FILES['image4']

        product.save()
        logger.info("Product updated | product_id=%s | name=%s", product_id, product.product_name)
        return JsonResponse({'success': True, 'message': 'Product updated successfully.'})

    return render(request, 'admin/products/product.html', {
        'product': product,
        'brands': brands,
        'categories': categories,
    })


def softdelete_product(request, product_id):
    logger.debug("softdelete_product called | product_id=%s", product_id)
    product = get_object_or_404(ProductDetails, product_id=product_id)
    product.is_deleted = True
    product.save()
    logger.info("Product soft-deleted | product_id=%s | name=%s", product_id, product.product_name)
    messages.success(request, 'Product successfully soft Unlisted!')
    return redirect('products:viewproducts')


def restoreproduct(request, product_id):
    logger.debug("restoreproduct called | product_id=%s", product_id)
    product = get_object_or_404(ProductDetails, product_id=product_id)
    product.is_deleted = False
    product.save()
    logger.info("Product restored | product_id=%s | name=%s", product_id, product.product_name)
    messages.success(request, 'Product successfully listed!')
    return redirect('products:viewproducts')


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff, 'accounts:admin_login')
def view_sizevariants(request, product_id):
    logger.debug("view_sizevariants called | product_id=%s", product_id)
    product = get_object_or_404(ProductDetails, product_id=product_id)
    variant_sizes = VariantSize.objects.filter(product=product).order_by('-size')
    logger.debug("Variants loaded for product | product_id=%s | count=%d", product_id, variant_sizes.count())
    return render(request, 'admin/products/variantsize.html', {
        'product': product,
        'variant_sizes': variant_sizes
    })


def add_sizevariants(request, product_id):
    logger.debug("add_sizevariants called | product_id=%s | method=%s", product_id, request.method)

    product = get_object_or_404(ProductDetails, product_id=product_id)

    if request.method == 'POST':
        size = request.POST.get('size')
        quantity = request.POST.get('quantity', '').strip()

        errors = {}

        if VariantSize.objects.filter(size__iexact=size, product=product).exists():
            errors['variant_error'] = 'This size variant already exists for this product.'

        try:
            quantity_int = int(quantity) if quantity else None
            if quantity_int is None or quantity_int <= 0:
                errors['quantity_error'] = 'Quantity must be a positive integer.'
        except (ValueError, TypeError):
            errors['quantity_error'] = 'Invalid quantity format.'

        if errors:
            logger.warning("Variant add failed | product_id=%s | size=%s | errors=%s", product_id, size, errors)
            return JsonResponse({'success': False, 'errors': errors})

        try:
            VariantSize.objects.create(product=product, size=size, qty=quantity_int)
            logger.info("Size variant added | product_id=%s | size=%s | qty=%d", product_id, size, quantity_int)
            return JsonResponse({'success': True, 'message': 'Size variant added successfully!'})
        except Exception as e:
            logger.error("Error adding variant | product_id=%s | error=%s", product_id, e, exc_info=True)
            return JsonResponse({'success': False, 'errors': {'server': 'Failed to add variant.'}})

    return render(request, 'admin/products/variantsize.html', {'product': product})


def edit_sizevariants(request, variant_id):
    logger.debug("edit_sizevariants called | variant_id=%s | method=%s", variant_id, request.method)

    variant = get_object_or_404(VariantSize, variant_id=variant_id)

    if request.method == 'POST':
        size = request.POST.get('size')
        quantity = request.POST.get('quantity', '').strip()

        errors = {}

        if VariantSize.objects.filter(size__iexact=size, product=variant.product).exclude(variant_id=variant_id).exists():
            errors['variant_error'] = 'This size variant already exists for this product.'

        try:
            quantity_int = int(quantity) if quantity else None
            if quantity_int is None or quantity_int <= 0:
                errors['quantity_error'] = 'Quantity must be greater than 0.'
        except (ValueError, TypeError):
            errors['quantity_error'] = 'Invalid quantity format.'

        if errors:
            logger.warning("Variant edit failed | variant_id=%s | errors=%s", variant_id, errors)
            return JsonResponse({'success': False, 'errors': errors})

        variant.size = size
        variant.qty = quantity_int
        variant.save()
        logger.info("Size variant updated | variant_id=%s | size=%s | qty=%d", variant_id, size, quantity_int)
        return JsonResponse({'success': True, 'message': 'Size variant updated successfully!'})

    return render(request, 'admin/products/edit_variantsize.html', {
        'variant': variant,
        'product': variant.product
    })


def soft_delete_variant(request, variant_id):
    logger.debug("soft_delete_variant called | variant_id=%s", variant_id)
    variant = get_object_or_404(VariantSize, variant_id=variant_id)
    variant.is_deleted = True
    variant.save()
    logger.info("Variant soft-deleted | variant_id=%s | size=%s", variant_id, variant.size)
    messages.success(request, 'Variant successfully Unlisted!')
    return redirect('products:view_sizevariants', product_id=variant.product.product_id)


def restore_variant(request, variant_id):
    logger.debug("restore_variant called | variant_id=%s", variant_id)
    variant = get_object_or_404(VariantSize, variant_id=variant_id)
    variant.is_deleted = False
    variant.save()
    logger.info("Variant restored | variant_id=%s | size=%s", variant_id, variant.size)
    messages.success(request, 'Variant successfully listed!')
    return redirect('products:view_sizevariants', product_id=variant.product.product_id)


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff, 'accounts:admin_login')
def single_product(request, product_id):
    logger.debug("single_product called | product_id=%s", product_id)
    product_details = ProductDetails.objects.get(product_id=product_id)
    logger.debug("Single product loaded | product_id=%s | name=%s", product_id, product_details.product_name)
    return render(request, 'admin/single_product.html', {'product_details': product_details})


def add_review(request, product_id):
    logger.debug("add_review called | product_id=%s | user=%s", product_id, request.user)

    if not request.user.is_authenticated:
        logger.warning("Review attempt without login | product_id=%s", product_id)
        messages.error(request, "You need to Login.")
        return redirect('accounts:login_user')

    if request.method == 'POST':
        user = request.user
        product = get_object_or_404(ProductDetails, product_id=product_id)

        if Review.objects.filter(product=product, user=user).exists():
            logger.info("Duplicate review blocked | user=%s | product_id=%s", user.username, product_id)
            messages.error(request, "You have already reviewed this product.")
            return redirect('userss:product_details', product_id=product_id)

        rating = request.POST.get('rating')
        review_text = request.POST.get('review', '')

        if not rating or not rating.isdigit():
            messages.error(request, "Invalid rating. Please select a valid number.")
            return redirect('userss:product_details', product_id=product_id)

        rating_int = int(rating)
        if rating_int < 1 or rating_int > 5:
            messages.error(request, "Rating must be between 1 and 5.")
            return redirect('userss:product_details', product_id=product_id)

        if not review_text.strip():
            messages.error(request, "Review text cannot be empty.")
            return redirect('userss:product_details', product_id=product_id)

        try:
            Review.objects.create(
                product=product,
                user=user,
                rating=rating_int,
                review=review_text
            )
            logger.info("Review added | user=%s | product_id=%s | rating=%d", user.username, product_id, rating_int)
            messages.success(request, "Your review has been submitted successfully.")
            return redirect('userss:product_details', product_id=product_id)
        except Exception as e:
            logger.error("Error adding review | product_id=%s | error=%s", product_id, e, exc_info=True)
            messages.error(request, "Failed to submit review.")
            return redirect('userss:product_details', product_id=product_id)

    return redirect('userss:product_details', product_id=product_id)


def delete_review(request, id):
    logger.debug("delete_review called | review_id=%s | user=%s", id, request.user)

    review = get_object_or_404(Review, id=id)
    product = get_object_or_404(ProductDetails, product_id=review.product.product_id)

    if review.user != request.user:
        logger.warning("Unauthorized review delete attempt | review_id=%s | user=%s", id, request.user)
        messages.info(request, "You are not allowed to delete this review.")
        return redirect('userss:product_details', product.product_id)

    review.delete()
    logger.info("Review deleted | review_id=%s | user=%s", id, request.user.username)
    messages.success(request, "Review deleted successfully.")
    return redirect('userss:product_details', product.product_id)