from django.shortcuts import render,redirect,get_object_or_404
from .models import Brand,Category,ProductDetails,VariantSize
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import never_cache
from django.db.models import F

def is_staff(user):
    return user.is_staff

def add_brands(request):
    if request.method=='POST':
        brand=request.POST.get('brandname')
        value=Brand.objects.create(brandname=brand)
        print(value)
        messages.success(request, 'Brand added successfully!')  
        return redirect('products:view_brands')
    return render(request,'admin/brand.html')


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff,'accounts:admin_login')
def view_brands(request):
    Brands=Brand.objects.all().order_by('is_deleted', '-created_at')
    return render(request,'admin/brand.html',{'brands':Brands})


def edit_brands(request,brand_id):
    Brands = get_object_or_404(Brand, brand_id=brand_id)

    if request.method == 'POST':
        brandname = request.POST.get('brandname')
        Brands.brandname = brandname
        Brands.save()  
        messages.success(request, 'Brand updated successfully!')  
        return redirect('products:view_brands')  
    return render(request, 'admin/brand.html', {'brands':Brands})



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

        value=Category.objects.create(category=category,category_type=categorytype)
        print(value)
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
    products = ProductDetails.objects.all()
    brands = Brand.objects.filter(is_deleted=False)
    categories = Category.objects.filter(is_deleted=False)

    return render(request, 'admin/products/product.html', {'products': products,'brands': brands,'categories': categories})


def addproducts(request):
    if request.method == 'POST':
        productname = request.POST.get('productname')
        description = request.POST.get('description')
        brand_name = request.POST.get('brandname')
        category_ids = request.POST.getlist('category')
        color = request.POST.get('color')
        occasion = request.POST.get('occasion')
        fit = request.POST.get('fit')

        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')
        image3 = request.FILES.get('image3')
        image4 = request.FILES.get('image4')

        try:
            brand = Brand.objects.get(brandname=brand_name)
        except Brand.DoesNotExist:
            brand = None

        product = ProductDetails.objects.create(
            product_name=productname,
            description=description,
            brand=brand,
            color=color,
            occasion=occasion,
            fit=fit,
            image1=image1,
            image2=image2,
            image3=image3,
            image4=image4
        )
        product.category.set(category_ids)  
        messages.success(request, 'Product added successfully!')  
        return redirect('products:viewproducts')  

    categories = Category.objects.filter(is_deleted=False)
    brands = Brand.objects.filter(is_deleted=False)
    return render(request, 'admin/products/product.html',{'categories': categories, 'brands': brands})


def editproduct(request, product_id):
    product = get_object_or_404(ProductDetails, product_id=product_id)

    brands = Brand.objects.filter(is_deleted=False)
    categories = Category.objects.filter(is_deleted=False)

    if request.method == 'POST':
        product.product_name = request.POST.get('product_name')
        if not product.product_name:
            messages.error(request, 'Product name cannot be empty.')
            return redirect('products:viewproducts')

        product.description = request.POST.get('description')

        brand_id = request.POST.get('brandname')
        product.brand_id = brand_id if brand_id else product.brand_id

        category_ids = request.POST.getlist('category')
        product.category.set(category_ids)
        product.color = request.POST.get('color')
        product.occasion = request.POST.get('occasion')
        product.fit = request.POST.get('fit')

        if 'image1' in request.FILES:
            product.image1 = request.FILES['image1']
        if 'image2' in request.FILES:
            product.image2 = request.FILES['image2']
        if 'image3' in request.FILES:
            product.image3 = request.FILES['image3']
        if 'image4' in request.FILES:
            product.image4 = request.FILES['image4']

        product.save()
        messages.success(request, 'Product updated successfully!')
        return redirect('products:viewproducts')

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
    variant_sizes = VariantSize.objects.filter(product=product)
    
    return render(request, 'admin/products/variantsize.html', {
        'product': product,
        'variant_sizes': variant_sizes
    })


def add_sizevariants(request, product_id):
    product = get_object_or_404(ProductDetails, product_id=product_id)

    if request.method == 'POST':
        size = request.POST.get('size')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')

        if size and price and quantity:
            VariantSize.objects.create(
                product=product,  
                size=size,
                price=price,
                qty=quantity
            )
            messages.success(request, 'Size variant added successfully!')
            return redirect('products:view_sizevariants', product_id=product_id)  
        else:
            messages.error(request, 'All fields are required.')

    return render(request, 'admin/products/variantsize.html', {'product': product})


def edit_sizevariants(request, variant_id):
    variant = get_object_or_404(VariantSize, variant_id=variant_id)

    if request.method == 'POST':
        size = request.POST.get('size')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')

        if size and price and quantity:
            variant.size = size
            variant.price = price
            variant.qty = quantity
            # variant.qty = F('qty') + quantity
            variant.save() 

            messages.success(request, 'Size variant updated successfully!')
            return redirect('products:view_sizevariants', product_id=variant.product.product_id)
        else:
            messages.error(request, 'All fields are required.')

    return render(request, 'admin/products/edit_variantsize.html', {
        'variant': variant,
        'product': variant.product
    })


def delete_sizevariant(request, variant_id):
    variant = get_object_or_404(VariantSize, variant_id=variant_id)

    if request.method == 'POST':
        variant.delete()  
        messages.success(request, f'Variant size {variant.size} has been permanently deleted!')
        return redirect('products:view_sizevariants', product_id=variant.product.product_id)
    

