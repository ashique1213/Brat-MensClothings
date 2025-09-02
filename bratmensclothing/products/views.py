from django.shortcuts import render,redirect,get_object_or_404
from .models import Brand,Category,ProductDetails,VariantSize,Review
from accounts.models import Users
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import never_cache
from django.db.models import F
from django.http import JsonResponse
from decimal import Decimal
from django.core.paginator import Paginator
from django.db.models import Q


def is_staff(user):
    return user.is_staff

def add_brands(request):
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
            return JsonResponse({'success': False, 'errors': errors})

        Brand.objects.create(brandname=brand)
        return JsonResponse({'success': True, 'message': 'Brand added successfully!'})

    return render(request, 'admin/brand.html')


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff,'accounts:admin_login')
def view_brands(request):

    search_query=request.GET.get('search','') 

    if search_query:
        Brands = Brand.objects.filter(
            brandname__icontains=search_query 
        ).order_by('is_deleted', '-created_at')
    else:
        Brands=Brand.objects.all().order_by('is_deleted', '-created_at')

    paginator = Paginator(Brands, 5)  
    page_number = request.GET.get('page') 
    Brands = paginator.get_page(page_number) 

    return render(request,'admin/brand.html',{'brands':Brands,'search_query':search_query})


def edit_brands(request, brand_id):
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
            return JsonResponse({'success': False, 'errors': errors})

        brand.brandname = brandname
        brand.save()
        
        return JsonResponse({'success': True, 'message': 'Brand updated successfully!'})

    return render(request, 'admin/brand.html', {'brand': brand})


def soft_delete_brand(request,brand_id):
    brand= get_object_or_404(Brand,brand_id=brand_id)
    brand.is_deleted=True
    brand.save()

    messages.success(request, 'Brand successfully Unlisted!')
    return redirect('products:view_brands')

def restore_brand(request,brand_id):
    brand= get_object_or_404(Brand,brand_id=brand_id)
    brand.is_deleted=False
    brand.save()
    messages.success(request, 'Brand successfully listed!')
    return redirect('products:view_brands')


def add_category(request):
    if request.method=='POST':
        category=request.POST.get('category')
        categorytype=request.POST.get('categorytype')

        Category.objects.create(category=category,category_type=categorytype)
        messages.success(request, 'Category added successfully!')  
        return redirect('products:view_category')
    return render(request,'admin/category.html')


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff,'accounts:admin_login')
def view_category(request):
    category=Category.objects.all().order_by('is_deleted', '-created_date')
    
    return render(request,'admin/category.html',{'category':category})


def soft_delete_category(request,category_id):
    category= get_object_or_404(Category,category_id=category_id)
    category.is_deleted=True 
    category.save()

    messages.success(request, 'Category successfully Unlisted!')
    return redirect('products:view_category')

def restore_category(request,category_id):
    category= get_object_or_404(Category,category_id=category_id)
    category.is_deleted=False
    category.save()
    messages.success(request, 'Category successfully listed!')
    return redirect('products:view_category')


def edit_category(request, category_id):
    category = get_object_or_404(Category, category_id=category_id)

    if request.method == 'POST':
        category_name = request.POST.get('category')
        category_type = request.POST.get('categorytype')
        category.category = category_name
        category.category_type = category_type
        category.save()  
        messages.success(request, 'Category updated successfully!')  
        return redirect('products:view_category')  
    return render(request, 'admin/category.html', {'category': category})



@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff,'accounts:admin_login')
def viewproducts(request):
    search_query=request.GET.get('search','')

    if search_query:
        products =ProductDetails.objects.filter(
            Q(product_name__icontains=search_query) | Q(category__category__icontains=search_query)|
            Q(brand__brandname__icontains=search_query)
        ).order_by('-created_at')   
    else:
        products = ProductDetails.objects.all().order_by('-created_at')

    brands = Brand.objects.filter(is_deleted=False)
    categories = Category.objects.filter(is_deleted=False)
    
    paginator=Paginator(products,4)
    page_number = request.GET.get('page')  
    products = paginator.get_page(page_number) 

    return render(request, 'admin/products/product.html', {'products': products,'brands': brands,'categories': categories,'search_query':search_query})


def addproducts(request):
    if request.method == 'POST':
        productname = request.POST.get('productname').strip()
        description = request.POST.get('description').strip()
        brand_name = request.POST.get('brandname')
        category_ids = request.POST.getlist('category')
        price = Decimal(request.POST.get('price', '0'))
        color = request.POST.get('color').strip()
        occasion = request.POST.get('occasion')
        fit = request.POST.get('fit')
        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')
        image3 = request.FILES.get('image3')
        image4 = request.FILES.get('image4')
        
        errors={}

        if not productname:
            errors['productname'] = 'Product name is required and cannot contain spaces.'
        elif ProductDetails.objects.filter(product_name__iexact=productname).exists():
            errors['productname'] = 'Product name already exists.'

        # Validation for description
        if not description:
            errors['description'] = 'Description is required.'
        elif len(description) < 10:
            errors['description'] = 'Description must be between 10 and 20 characters.'

        try:
            price = Decimal(price)
            if price < 400:
                errors['price'] = 'Price must be a number greater than or equal to 400.'
        except:
            errors['price'] = 'Price must be a valid number.'

        if not color:
            errors['color'] = 'Color is required and cannot be empty.'
        elif ' ' in color:
            errors['color'] = 'Color cannot contain spaces.'

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        try:
            brand = Brand.objects.get(brandname=brand_name)
        except Brand.DoesNotExist:
            brand = None

        product = ProductDetails.objects.create(
            product_name=productname,
            description=description, 
            brand=brand,
            price=price,
            color=color,
            occasion=occasion,
            fit=fit,
            image1=image1,
            image2=image2,
            image3=image3,
            image4=image4
        )
        product.category.set(category_ids)  
        # messages.success(request, 'Product added successfully!')  
        # return redirect('products:viewproducts') 
        return JsonResponse({'success': True, 'message': 'Product added successfully!'}) 

    categories = Category.objects.filter(is_deleted=False)
    brands = Brand.objects.filter(is_deleted=False)
    return render(request, 'admin/products/product.html',{'categories': categories, 'brands': brands})


def editproduct(request, product_id):
    product = get_object_or_404(ProductDetails, product_id=product_id)

    brands = Brand.objects.filter(is_deleted=False)
    categories = Category.objects.filter(is_deleted=False)

    if request.method == 'POST':
        errors = {}

        product.product_name = request.POST.get('product_name').strip()
        
        if not product.product_name:
            errors['productname'] = 'Product name is required and cannot contain spaces.'
        elif ProductDetails.objects.filter(product_name__iexact=product.product_name).exclude(product_id=product.product_id).exists():
            errors['productname'] = 'Product name already exists.'

        product.description = request.POST.get('description').strip()

        if not product.description:
            errors['description'] = 'Description is required.'
        elif len(product.description) < 10 :
            errors['description'] = 'Description must be between 10 and 500 characters.'

        brand_id = request.POST.get('brandname')
        product.brand_id = brand_id if brand_id else product.brand_id

        category_ids = request.POST.getlist('category')
        product.category.set(category_ids)
        product.color = request.POST.get('color').strip()
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

        # Return errors if any
        if errors:
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
        # messages.success(request, 'Product updated successfully!')
        # return redirect('products:viewproducts')
        return JsonResponse({'success': True, 'message': 'Product updated successfully.'})

    return render(request, 'admin/products/product.html', {
        'product': product,
        'brands': brands,
        'categories': categories,
    })


def softdelete_product(request, product_id):
    product = get_object_or_404(ProductDetails, product_id=product_id)
    product.is_deleted = True
    product.save()
    messages.success(request, 'Product successfully soft Unlisted!')
    return redirect('products:viewproducts')


def restoreproduct(request, product_id):
    product = get_object_or_404(ProductDetails, product_id=product_id)
    product.is_deleted = False
    product.save()
    messages.success(request, 'Product successfully listed!')
    return redirect('products:viewproducts')


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff,'accounts:admin_login')
def view_sizevariants(request, product_id):
    product = get_object_or_404(ProductDetails, product_id=product_id)
    variant_sizes = VariantSize.objects.filter(product=product).order_by('-size')
    
    return render(request, 'admin/products/variantsize.html', {
        'product': product,
        'variant_sizes': variant_sizes
    })


def add_sizevariants(request, product_id):
    product = get_object_or_404(ProductDetails, product_id=product_id)

    if request.method == 'POST':
        size = request.POST.get('size')
        quantity = request.POST.get('quantity').strip()

        errors={}
        
        if VariantSize.objects.filter(size__iexact=size, product=product).exists():
            errors['variant_error'] = 'This size variant already exists for this product.'
        
        try:
            quantity = int(quantity) if quantity else None
            if quantity is None or quantity <= 0:
                errors['quantity_error'] = 'Quantity must be a positive integer.'
        
        except (ValueError, TypeError):
            errors['quantity_error'] = 'Invalid quantity format.'

        if errors:
            return JsonResponse({'success': False, 'errors': errors})
        
        if size and quantity:
            VariantSize.objects.create(
                product=product,  
                size=size,
                qty=quantity
            )
            # messages.success(request, 'Size variant added successfully!')
            # return redirect('products:view_sizevariants', product_id=product_id) 
            return JsonResponse({'success': True, 'message': 'Size variant added successfully!'}) 
        else:
            messages.error(request, 'All fields are required.')

    return render(request, 'admin/products/variantsize.html', {'product': product})


def edit_sizevariants(request, variant_id):
    variant = get_object_or_404(VariantSize, variant_id=variant_id)

    if request.method == 'POST':
        size = request.POST.get('size')
        quantity = request.POST.get('quantity').strip()

        errors = {}

        if VariantSize.objects.filter(size__iexact=size, product=variant.product).exclude(variant_id=variant.variant_id).exists():
            errors['variant_error'] = 'This size variant already exists for this product.'
        
        # Validate quantity field
        try:
            quantity = int(quantity) if quantity else None
            if quantity is None or quantity <= 0:
                errors['quantity_error'] = 'Quantity must be greater than 0.'
        except (ValueError, TypeError):
            errors['quantity_error'] = 'Invalid quantity format.'
        
        # Return errors if any
        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        # If no errors, update the variant
        if size and quantity:
            variant.size = size
            variant.qty = quantity 
            variant.save()

            return JsonResponse({'success': True, 'message': 'Size variant updated successfully!'})

    return render(request, 'admin/products/edit_variantsize.html', {
        'variant': variant,
        'product': variant.product
    })


def soft_delete_variant(request,variant_id):
    variant= get_object_or_404(VariantSize,variant_id=variant_id)
    variant.is_deleted=True 
    variant.save()

    messages.success(request, 'Variant successfully Unlisted!')
    return redirect('products:view_sizevariants',product_id=variant.product.product_id)

def restore_variant(request,variant_id):
    variant= get_object_or_404(VariantSize,variant_id=variant_id)
    variant.is_deleted=False 
    variant.save()

    messages.success(request, 'Variant successfully listed!')
    return redirect('products:view_sizevariants',product_id=variant.product.product_id)



@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff,'accounts:admin_login')
def single_product(request,product_id):
    product_details=ProductDetails.objects.get(product_id=product_id)

    return render(request,'admin/single_product.html',{'product_details':product_details})


def add_review(request, product_id):
    if request.user.is_authenticated:
        if request.method == 'POST':
            user = request.user
            product = get_object_or_404(ProductDetails, product_id=product_id)

            if Review.objects.filter(product=product, user=user).exists():
                messages.error(request, "You have already reviewed this product.")
                return redirect('userss:product_details', product_id=product_id)

            rating = request.POST.get('rating')
            review = request.POST.get('review')


            if not rating or not rating.isdigit():
                messages.error(request, "Invalid rating. Please select a valid number.")
                return redirect('userss:product_details', product_id=product_id)

            rating = int(rating)
            if rating < 1 or rating > 5:
                messages.error(request, "Rating must be between 1 and 5.")
                return redirect('userss:product_details', product_id=product_id)

            if not review.strip():
                messages.error(request, "Review text cannot be empty.")
                return redirect('userss:product_details', product_id=product_id)

            Review.objects.create(
                product=product,
                user=user,
                rating=rating,
                review=review
            )

            messages.success(request, "Your review has been submitted successfully.")
            return redirect('userss:product_details', product_id=product_id)

        return redirect('userss:product_details', product_id=product_id)
    
    messages.error(request, "You need to Login.")
    return redirect('accounts:login_user')


def delete_review(request,id):
    review=get_object_or_404(Review,id=id)
    product=get_object_or_404(ProductDetails,product_id=review.product.product_id)
    if review.user != request.user:
        messages.info(request, "You are not allowed to delete this review.")
        return redirect('userss:product_details',product.product_id)
    review.delete()
        
    messages.success(request, "Review deleted successfully.")
    return redirect('userss:product_details',product.product_id)
