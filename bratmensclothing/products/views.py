from django.shortcuts import render,redirect,get_object_or_404
from .models import Brand,Category,Product,Variant
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import never_cache



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


def add_products(request):
    if request.method == 'POST':
        productname = request.POST.get('productname')
        description = request.POST.get('description')
        brand = request.POST.get('brandname')
        category_ids = request.POST.getlist('category')  

        try:
            brand = Brand.objects.get(brandname=brand)
        except Brand.DoesNotExist:
            brand = None  

        product = Product.objects.create(
            product_name=productname,
            description=description,
            brand=brand
        ) 
        product.category.set(category_ids)  
        messages.success(request, 'Product added successfully!')  
        return redirect('products:view_products')  
    # categories = Category.objects.all()
    categories = Category.objects.filter(is_deleted=False)
    # brands = Brand.objects.all()
    brands = Brand.objects.filter(is_deleted=False)
    return render(request, 'admin/product.html', {'categories': categories, 'brands': brands})


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff,'accounts:admin_login')
def view_products(request):
    products=Product.objects.all().order_by('is_deleted', '-created_at')
    # products = Product.objects.filter(brand__is_deleted=False, category__is_deleted=False).order_by('is_deleted', '-created_at')

    # brands = Brand.objects.all()
    brands = Brand.objects.filter(is_deleted=False)
    # categories = Category.objects.all()
    categories = Category.objects.filter(is_deleted=False)


    return render(request,'admin/product.html',{'products':products ,'brands': brands,'categories': categories})



def edit_product(request, product_id):
    products = get_object_or_404(Product, product_id=product_id)
    # brands = Brand.objects.all() 
    brands = Brand.objects.filter(is_deleted=False)
    # categories = Category.objects.all() 
    categories = Category.objects.filter(is_deleted=False)


    if request.method == 'POST':
        products.product_name = request.POST.get('product_name')
        products.description = request.POST.get('description')
        products.brand_id = request.POST.get('brandname')  
        category_id = request.POST.get('category')
        
        if category_id:
            products.category.set([category_id]) 
        products.save()  
        messages.success(request, 'Product updated successfully!')  
        return redirect('products:view_products') 
    return render(request, 'admin/product.html', {'products': products,'brands': brands,'categories': categories,})


def soft_delete_product(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    product.is_deleted = True
    product.save()
    messages.success(request, 'Product successfully soft Unlisted!')
    return redirect('products:view_products')


def restore_product(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    product.is_deleted = False
    product.save()
    messages.success(request, 'Product successfully listed!')
    return redirect('products:view_products') 


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff,'accounts:admin_login')
def add_variants(request,product_id):
    product=get_object_or_404(Product,product_id=product_id)

    if request.method=='POST':
        image1=request.FILES.get('image1')
        image2=request.FILES.get('image2')
        image3=request.FILES.get('image3')
        image4=request.FILES.get('image4')
        size = request.POST.getlist('sizes[]')
        color = request.POST.get('colors')
        occation = request.POST.get('occasions')
        fit = request.POST.get('fit')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')

        variant = Variant(
            image1=image1,
            image2=image2,
            image3=image3,
            image4=image4,
            size=size,
            color=color,
            occation=occation,
            fit=fit,
            price=price,
            qty=quantity,
            status=True,  
            product=product,  
        )
        variant.save()
        messages.success(request, 'Variant added successfully!')
        return redirect('products:view_variants', product_id=product_id)
    return render(request,'admin/add_variants.html', {'product': product})


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff,'accounts:admin_login')
def view_variants(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    variants = Variant.objects.filter(product=product)
    variants_added = variants.exists()
    return render(request, 'admin/variants.html', {'product': product, 'variants': variants,'variants_added': variants_added})


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff,'accounts:admin_login')
def edit_variants(request,product_id):
    product=get_object_or_404(Product,product_id=product_id)
    variant=get_object_or_404(Variant,product=product)

    if request.method=='POST':
        if request.FILES.get('image1'):
            variant.image1 = request.FILES['image1']
        if request.FILES.get('image2'):
            variant.image2 = request.FILES['image2']
        if request.FILES.get('image3'):
            variant.image3 = request.FILES['image3']
        if request.FILES.get('image4'):
            variant.image4 = request.FILES['image4']

        variant.size = request.POST.getlist('sizes[]')
        variant.color = request.POST.get('colors')
        variant.occation = request.POST.get('occasions')
        variant.fit = request.POST.get('fit')
        variant.qty = request.POST.get('quantity', variant.qty)
        variant.price = request.POST.get('price', variant.price)

        variant.save()
        messages.success(request, 'Variant updated successfully!')
        return redirect('products:view_variants', product_id=product_id)
    return render(request, 'admin/edit_variants.html', {'product': product,'variant': variant})


def delete_variants(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)

    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        if not variant_id: 
            return redirect('products:view_variants', product_id=product_id)
        variant = get_object_or_404(Variant, variant_id=variant_id, product=product)
        variant.delete()

        messages.success(request, 'Reset successfully!')
        return redirect('products:view_variants', product_id=product_id)
    variants = Variant.objects.filter(product=product)
    return render(request, 'admin/variants.html', {'product': product, 'variants': variants})


