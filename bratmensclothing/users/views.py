from django.shortcuts import render,redirect,get_object_or_404
from accounts.models import Users
from products.models import ProductDetails
from django.contrib import messages
from products.models import Category,Brand
from .models import Address
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import never_cache
from django.db.models import Q


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
 
    return render(request, 'user/accountdetails.html', {'user': user})

@never_cache
def edit_account_details(request, userid):
    userdetails = get_object_or_404(Users, userid=userid)

    if request.method == 'POST':
        email = request.POST.get('email').strip()
        username = request.POST.get('username').strip()
        phone = request.POST.get('phone').strip()
        
        userdetails.email = email
        userdetails.username = username
        userdetails.phone_number = phone
        
        userdetails.save() 
        
        messages.success(request, 'Your account details have been updated successfully.')
        
        return redirect('userss:accountdetails',userid=userid)  

    return render(request, 'user/edit_account.html', {'user': userdetails})



@never_cache
def address_details(request, userid):
    user = get_object_or_404(Users, userid=userid)
    addresses = Address.objects.filter(user=user)

    return render(request, 'user/address.html', {'addresses': addresses})


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
        return redirect('userss:addressdetails',userid=userid)
    
    return render(request,'user/add_address.html')


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

        address.save()
        messages.success(request, 'Your Address details have been updated successfully.')

        return redirect('userss:addressdetails', userid=user_id)

    return render(request, 'user/edit_address.html', {'address': address})

