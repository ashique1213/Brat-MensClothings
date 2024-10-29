from django.shortcuts import render,redirect,get_object_or_404
from accounts.models import Users
from products.models import ProductDetails
from django.contrib import messages
from products.models import Category,Brand
from .models import Address
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import never_cache
from django.db.models import Q
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import check_password
import re


def is_staff(user):
    return user.is_staff


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff,'accounts:admin_login')
def view_user(request):
    users=Users.objects.filter(is_superuser=False)

    return render(request,'admin/users.html',{'users':users})


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
    products=(
        ProductDetails.objects.select_related('brand')
        .prefetch_related('category','variants')
        .filter(
            Q(is_deleted=False),
            Q(brand__is_deleted=False),
            Q(category__is_deleted=False)
        )

    )
    return render(request,'user/categorylist.html',{'products':products})


def product_details(request, product_id):
    product = get_object_or_404(ProductDetails, product_id=product_id, is_deleted=False)
    products=(
        ProductDetails.objects.select_related('brand')
        .prefetch_related('category','variants')
        .filter(
            Q(is_deleted=False),
            Q(brand__is_deleted=False),
            Q(category__is_deleted=False)
        )

    )  
    return render(request, 'user/productdetails.html', 
        {
            'product': product,
            'products':products
         })



@never_cache
def account_details(request,userid):
    user = get_object_or_404(Users, userid=userid)
 
    return render(request, 'user/accountdetails.html', {'user':user})

@never_cache
def edit_account_details(request, userid):
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
def reset_password(request, userid):
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
        messages.success(request, 'Your password has been reset successfully.')
        return redirect('userss:accountdetails',userid=userid)

    return render(request, 'user/reset_password.html', {'user': user})

@never_cache
def address_details(request, userid):
    user = get_object_or_404(Users, userid=userid)
    addresses = Address.objects.filter(user=user)

    return render(request, 'user/address.html', {'addresses': addresses,'user':user})


@never_cache
def add_address(request,userid):
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
    address.delete() 
    messages.success(request, 'Address has been successfully deleted.')
    return redirect('userss:addressdetails', userid=user_id) 


@never_cache
def edit_address(request, id):
    address = get_object_or_404(Address, id=id)
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



