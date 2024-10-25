from django.shortcuts import render,redirect,get_object_or_404
from accounts.models import Users
from django.contrib import messages
from products.models import Variant,Product,Category,Brand
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import never_cache



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


def category_details(request):
    variants = Variant.objects.select_related('product__brand').prefetch_related('product__category').all()

    return render(request,'user/categorylist.html',{'variants':variants})


def product_details(request, product_id):
    productdetails = get_object_or_404(Product, product_id=product_id)
    varaints=Variant.objects.filter(product=productdetails)
    allvariants=Variant.objects.select_related('product__brand').prefetch_related('product__category').all()
    return render(request, 'user/productdetails.html', 
                  {'productdetails': productdetails,'varaints':varaints,'allvariants':allvariants})


