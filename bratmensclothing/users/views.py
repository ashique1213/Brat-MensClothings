from django.shortcuts import render,redirect,get_object_or_404
from accounts.models import Users
from products.models import ProductDetails,VariantSize,Review
from django.contrib import messages
from products.models import Category,Brand
from .models import Address
from django.http import Http404
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import never_cache
from django.db.models import Q,Min  
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import check_password
import re
from datetime import timezone   
from offer.models import Brand_Offers,Product_Offers
from django.utils import timezone
from django.db.models import Q, Sum, Min, Avg
from django.views.decorators.cache import cache_control
from django.core.paginator import Paginator
from coupon.models import Coupon
import cloudinary.uploader
from decimal import Decimal
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Avg, IntegerField
from django.db.models.functions import Cast


def is_staff(user):
    return user.is_staff

@never_cache
def error(request):
    return render(request,'user/404.html')
    

@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff,'accounts:admin_login')
def view_user(request):
    search_query=request.GET.get('search','') 
    
    if search_query:
        users=Users.objects.filter(
            Q(username__icontains=search_query) | Q(email__icontains=search_query),
            is_superuser=False
        ).order_by('-date_joined')
    else:
        users=Users.objects.filter(is_superuser=False).order_by('-date_joined')
    
    paginator=Paginator(users,5)
    page_number=request.GET.get('page')
    users=paginator.get_page(page_number)

    return render(request,'admin/users.html',{'users':users,'search_query': search_query})


def block_user(request,userid):
    users=get_object_or_404(Users,userid=userid)
    users.is_active=True
    users.save()
    messages.success(request,'User Blocked Succesfully')
    return redirect('userss:view_user')


def unblock_user(request,userid):
    users=get_object_or_404(Users,userid=userid)
    users.is_active=False
    users.save()
    messages.success(request,'User Un-Blocked Succesfully')
    return redirect('userss:view_user')


@never_cache
def category_details(request):
    sort_option=request.GET.get('sort','')
    query = request.GET.get('search', '')



    selected_categories = request.GET.getlist('category')
    selected_brands = request.GET.getlist('brand')
    selected_colors = request.GET.getlist('color')
    selected_sizes = request.GET.getlist('size')

    products=(
        ProductDetails.objects.select_related('brand')
        .prefetch_related('category','variants','Rating')
        .filter(
            Q(is_deleted=False),
            Q(brand__is_deleted=False),
            Q(category__is_deleted=False)
        )
        .annotate(
        total_quantity=Sum('variants__qty'),
        average_rating=Cast(Avg('Rating__rating'), IntegerField())
        )
    )

    if selected_categories:
        products = products.filter(category__category_id__in=selected_categories)
    
    # Filter by brands
    if selected_brands:
        products = products.filter(brand__brand_id__in=selected_brands)
    
    # Filter by colors
    if selected_colors:
        products = products.filter(color__in=selected_colors)
    
    # Filter by sizes
    if selected_sizes:
        products = products.filter(variants__size__in=selected_sizes)
   
    if query:
        query_terms = query.split()
        q_filter = Q()
        
        for term in query_terms:
            q_filter |= (Q(product_name__icontains=term) |
                         Q(description__icontains=term) |
                         Q(color__icontains=term) |
                         Q(occasion__icontains=term) |
                         Q(fit__icontains=term)|
                         Q(brand__brandname__icontains=term)|
                         Q(category__category__icontains=term))
                         
        products = products.filter(q_filter)

    if sort_option == 'newly_added':
        products = products.order_by('-created_at')  
    elif sort_option == 'atoz':
        products = products.order_by('product_name') 
    elif sort_option == 'ztoa':
        products = products.order_by('-product_name')  
    elif sort_option == 'lowest_price':
        products = products.annotate(lowest_price=Min('price')).order_by('lowest_price') 
    elif sort_option == 'highest_price':
        products = products.annotate(lowest_price=Min('price')).order_by('-lowest_price')
    else: 
        products = products.order_by('updated_at')
    

    for product in products:
        product_offer = Product_Offers.objects.filter(
            product_id=product,
            status=True,
            started_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).first()
        
        brand_offer = Brand_Offers.objects.filter(
            brand_id=product.brand,
            status=True,
            started_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).first()
        
        final_price = product.price
        discount_percentage = 0

        # Determine the highest applicable offer
        if product_offer and brand_offer:
            if product_offer.offer_price > brand_offer.offer_price:
                final_price = product.price - product_offer.offer_price
                discount_percentage = (product_offer.offer_price / product.price) * Decimal(100)
            else:
                final_price = product.price - brand_offer.offer_price
                discount_percentage = (brand_offer.offer_price / product.price) * Decimal(100)
        elif product_offer:
            final_price = product.price - product_offer.offer_price
            discount_percentage = (product_offer.offer_price / product.price) * Decimal(100)
        elif brand_offer:
            final_price = product.price - brand_offer.offer_price
            discount_percentage = (brand_offer.offer_price / product.price) * Decimal(100)

        product.final_price = final_price
        product.discount_percentage = discount_percentage


        
    categories=Category.objects.all()
    Brands=Brand.objects.all()
    Variants = VariantSize.objects.values('size').distinct().order_by('size')
    colors = ProductDetails.objects.values_list('color', flat=True).distinct()

    items_per_page = 9    
    paginator = Paginator(products, items_per_page)
    page_number = request.GET.get('page', 1)
    try:
        paginated_products = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_products = paginator.page(1)
    except EmptyPage:
        paginated_products = paginator.page(paginator.num_pages)

    return render(request,'user/categorylist.html',
                  {
                      'products':paginated_products,
                      'categories':categories,
                      'Brands':Brands,
                      'Variants':Variants,
                      'sort':sort_option,
                      'query':query,
                      'colors':colors,
                      'selected_categories': selected_categories,
                      'selected_brands': selected_brands,
                      'selected_colors': selected_colors,
                      'selected_sizes': selected_sizes,
                })


@cache_control(private=True, no_cache=True)
def product_details(request, product_id):
    product = get_object_or_404(ProductDetails, product_id=product_id, is_deleted=False)

    product_reviews=Review.objects.filter(product=product_id).order_by('-created_at')[:6]
    rating_count = Review.objects.filter(product_id=product_id).count() 
    avg_rating = Review.objects.filter(product_id=product_id).aggregate(average_rating=Avg('rating'))['average_rating']
    rounded_avg_rating = round(avg_rating * 2) / 2 if avg_rating else 0
    
    # product offer
    product_offer = Product_Offers.objects.filter(
        product_id=product,
        status=True,
        started_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).first()
    
    # brand offer
    brand_offer = Brand_Offers.objects.filter(
        brand_id=product.brand,
        status=True,
        started_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).first()
    

    if product_offer and product_offer.offer_price > 0 and brand_offer and brand_offer.offer_price > 0:
         
        if product_offer.offer_price > brand_offer.offer_price:
            final_price = product.price - product_offer.offer_price
            discount_percentage = (product_offer.offer_price / product.price) * 100
        
        else:
            final_price = product.price - brand_offer.offer_price
            discount_percentage = (brand_offer.offer_price / product.price) * 100

    elif product_offer and product_offer.offer_price > 0:
        
        final_price = product.price - product_offer.offer_price
        discount_percentage = (product_offer.offer_price / product.price) * 100
    
    elif brand_offer and brand_offer.offer_price > 0:
        final_price = product.price - brand_offer.offer_price
        discount_percentage = (brand_offer.offer_price / product.price) * 100
    
    else:
        final_price = product.price
        discount_percentage = 0

    products = (
        ProductDetails.objects.select_related('brand')
        .prefetch_related('category', 'variants','Rating')
        .filter(
            Q(is_deleted=False),
            Q(brand__is_deleted=False),
            Q(category__is_deleted=False)
        )
        .annotate(
        average_rating=Avg('Rating__rating')    
    )
    )
    
    # coupons = Coupon.objects.filter(is_active=False,usage_limit__gt=0)
    coupons = Coupon.objects.filter(
            is_active=False,                    
            usage_limit__gt=0,                 
            valid_from__lte=timezone.now().date(),
            valid_to__gte=timezone.now().date()
        )
    return render(request, 'user/productdetails.html', {
        'product': product,
        'products': products,
        'coupons': coupons,
        'final_price': final_price,
        'discount_percentage': discount_percentage,
        'product_reviews':product_reviews,
        'rating_count':rating_count,
        'avg_rating':rounded_avg_rating
    })



@never_cache
@login_required(login_url='accounts:login_user')
def account_details(request,userid):
    if request.user.userid != userid:
        return redirect('userss:error')

    user = get_object_or_404(Users, userid=userid)
 
    return render(request, 'user/accountdetails.html', {'user':user})



@never_cache
@login_required(login_url='accounts:login_user')
def add_profile(request, userid):
    user = get_object_or_404(Users, userid=userid)

    if request.user.userid != user.userid:
        return redirect('userss:error')

    if request.method == 'POST':
        profile_image = request.FILES.get('profile')

        if profile_image:
            user.profile = profile_image
            user.save()
            messages.success(request, 'Profile image has been successfully added.')
            return redirect('userss:accountdetails', userid=userid)
        else:
            return render(request, 'user/accountdetails.html', {'user': user, 'error': 'No image uploaded.'})

    return render(request, 'user/accountdetails.html', {'user': user})


@never_cache
@login_required(login_url='accounts:login_user')
def delete_profile(request, userid):
    user = get_object_or_404(Users, userid=userid)

    if user.profile:
        public_id = user.profile.public_id 
        cloudinary.uploader.destroy(public_id)
        user.profile = None
        user.save()
    messages.success(request, 'Profile image has been successfully deleted.')
    return redirect('userss:accountdetails', userid=userid)



@never_cache
@login_required(login_url='accounts:login_user')
def edit_account_details(request, userid):
    if request.user.userid != userid:
        return redirect('userss:error')

    userdetails = get_object_or_404(Users, userid=userid)

    if request.method == 'POST':
        email = request.POST.get('email').strip()
        username = request.POST.get('username').strip()
        phone = request.POST.get('phone').strip()

        errors = {}

        if not username:
            errors['username_error'] = 'Username is required.'
        elif any(char.isdigit() or char.isspace() for char in username):
            errors['username_error'] = 'Username should not contain numbers or spaces.'
        elif len(username) < 3:
            errors['username_error'] = 'Username must be at least 3 characters long.'
        elif Users.objects.filter(username=username).exclude(userid=userid).exists():
            errors['username_error'] = 'This username is already taken.'

        if not email:
            errors['email_error'] = 'Email is required.'
        else:
            try:
                validate_email(email)  
            except ValidationError:
                errors['email_error'] = 'Enter a valid email address.'

            if Users.objects.filter(email=email).exclude(userid=userid).exists():
                errors['email_error'] = 'This email is already in use.'
    

        if Users.objects.filter(email=email).exclude(userid=userid).exists():
            errors['email_error'] = 'This email is already in use.'

        if phone: 
            if not re.match(r'^\+?[1-9]\d{1,14}$', phone):  
                errors['phone_error'] = 'Enter a valid phone number.'
            elif Users.objects.filter(phone_number=phone).exclude(userid=userid).exists():
                errors['phone_error'] = 'This phone number is already in use.'

        if errors:
            return render(request, 'user/edit_account.html', {'errors': errors, 'user': userdetails})
        
        userdetails.email = email
        userdetails.username = username
        userdetails.phone_number = phone
        
        userdetails.save() 
        
        messages.success(request, 'Your account details have been updated successfully.')
        
        return redirect('userss:accountdetails',userid=userid)  

    return render(request, 'user/edit_account.html', {'user': userdetails})


@never_cache
@login_required(login_url='accounts:login_user')
def reset_password(request, userid):
    if request.user.userid != userid:
        return redirect('userss:error')
    
    user = get_object_or_404(Users, userid=userid)

    if request.method == 'POST':
        old_password = request.POST.get('oldpassword').strip()
        new_password = request.POST.get('newpassword1').strip()
        confirm_password = request.POST.get('newpassword2').strip()

        errors = {}

        if not old_password:
            errors['old_password_error'] = 'Old password is required.'
        elif not check_password(old_password, user.password):
            errors['old_password_error'] = 'Old password does not match.'

        if not new_password:
            errors['password_error'] = 'New password is required.'
        else:
            if len(new_password) < 6:
                errors['password_error'] = 'Password must be at least 6 characters long.'
            if not re.search(r'[A-Z]', new_password):
                errors['password_error'] = 'Password must include at least one uppercase letter.'
            if not re.search(r'[a-z]', new_password):
                errors['password_error'] = 'Password must include at least one lowercase letter.'
            if not re.search(r'[0-9]', new_password):
                errors['password_error'] = 'Password must include at least one digit.'
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
                errors['password_error'] = 'Password must include at least one special character.'

        if new_password != confirm_password:
            errors['confirm_password_error'] = 'Passwords do not match.'

        if errors:
            return render(request, 'user/reset_password.html', {'errors': errors, 'user': user})

        user.set_password(new_password)
        user.save()
        messages.success(request, 'Your password has been reset successfully.PLEASE LOGIN')
        return redirect('accounts:login_user')

    return render(request, 'user/reset_password.html', {'user': user})


@never_cache
@login_required(login_url='accounts:login_user')
def address_details(request, userid):
    if request.user.userid != userid:
        return redirect('userss:error')
    
    user = get_object_or_404(Users, userid=userid)
    addresses = Address.objects.filter(user=user,status=False)

    return render(request, 'user/address.html', {'addresses': addresses,'user':user})


@never_cache
@login_required(login_url='accounts:login_user')
def add_address(request,userid):
    if request.user.userid != userid:
        return redirect('userss:error')
    
    user_id=get_object_or_404(Users,userid=userid)

    if request.method=='POST':
        address=request.POST.get('address').strip()
        street=request.POST.get('street').strip()
        landmark=request.POST.get('landmark').strip()
        city=request.POST.get('city').strip()
        pincode=request.POST.get('pincode').strip()
        district=request.POST.get('district').strip()
        state=request.POST.get('state').strip()
        
        errors = {}

        if not address:
            errors['address_error'] = 'Address is required.'
        elif len(address) < 10:
            errors['address_error'] = 'Address must be at least 100 characters long.'

        if not street:
            errors['street_error'] = 'Street is required.'
        elif len(street) < 3:
            errors['street_error'] = 'Street must be at least 3 characters long.'

        if not landmark:
            errors['landmark_error'] = 'Landmark is required.'
        elif len(landmark) < 3:
            landmark['landmark_error'] = 'Landmark must be at least 3 characters long.'

        if not city:
            errors['city_error'] = 'City is required.'
        elif len(city) < 3:
            errors['city_error'] = 'City must be at least 3 characters long.'

        pincode_regex = RegexValidator(regex=r'^\d{6}$', message='Pincode must be a 6-digit number.')
        try:
            pincode_regex(pincode)
        except ValidationError:
            errors['pincode_error'] = 'Pincode must be a valid 6-digit number.'

        if not state:
            errors['state_error'] = 'State is required.'
        elif len(state) < 3:
            errors['state_error'] = 'State must be at least 3 characters long.'

        if errors:
            return render(request, 'user/add_address.html', {'errors': errors, 'user':user_id})

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
        messages.success(request, 'Address added successfully.')
        return redirect('userss:addressdetails',userid=userid)
    
    return render(request,'user/add_address.html',{'user':user_id})


@never_cache
def remove_address(request, id):
    address = get_object_or_404(Address, id=id) 
    user_id = address.user.userid  
    address.status=True
    address.save()
    messages.success(request, 'Address has been successfully deleted.')
    return redirect('userss:addressdetails', userid=user_id) 


@never_cache
@login_required(login_url='accounts:login_user')
def edit_address(request, id):
    try:
        address = get_object_or_404(Address, id=id)
    except Http404:
        return redirect('userss:error')
    user_id = address.user.userid 

    if request.method == 'POST':
        addres = request.POST.get('address').strip()
        street = request.POST.get('street').strip()
        landmark = request.POST.get('landmark').strip()
        city = request.POST.get('city').strip()
        pincode = request.POST.get('pincode').strip()
        district = request.POST.get('district').strip()
        state = request.POST.get('state').strip()

        address.address = addres
        address.street = street
        address.landmark = landmark
        address.city = city
        address.pincode = pincode
        address.district = district
        address.state = state

        errors = {}

        if not addres:
            errors['address_error'] = 'Address is required.'
        elif len(addres) < 10:
            errors['address_error'] = 'Address must be at least 10 characters long.'

        if not street:
            errors['street_error'] = 'Street is required.'
        elif len(street) < 3:
            errors['street_error'] = 'Street must be at least 3 characters long.'

        if not landmark:
            errors['landmark_error'] = 'Landmark is required.'
        elif len(landmark) < 3:
            landmark['landmark_error'] = 'Landmark must be at least 3 characters long.'

        if not city:
            errors['city_error'] = 'City is required.'
        elif len(city) < 3:
            errors['city_error'] = 'City must be at least 3 characters long.'

        pincode_regex = RegexValidator(regex=r'^\d{6}$', message='Pincode must be a 6-digit number.')
        try:
            pincode_regex(pincode)
        except ValidationError:
            errors['pincode_error'] = 'Pincode must be a valid 6-digit number.'

        if not state:
            errors['state_error'] = 'State is required.'
        elif len(state) < 3:
            errors['state_error'] = 'State must be at least 3 characters long.'

        if errors:
            return render(request, 'user/edit_address.html', {'address': address, 'errors': errors})

        address.save()
        messages.success(request, 'Your Address details have been updated successfully.')

        return redirect('userss:addressdetails', userid=user_id)

    return render(request, 'user/edit_address.html', {'address': address})


@never_cache
def about(req):

    return render(req,'user/about_us.html')
@never_cache
def contact(req):

    return render(req,'user/contact_us.html')