from django.shortcuts import render,redirect,get_object_or_404
from accounts.models import Users
from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import never_cache
import re
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from decimal import Decimal
from django.core.paginator import Paginator
from .models import Coupon


def is_staff(user):
    return user.is_staff

@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff, 'accounts:admin_login')
def coupon_details(request):
    coupons = Coupon.objects.all()
    return render(request, 'admin/coupon.html', {'coupons': coupons})

@never_cache
def add_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        discount_amount = request.POST.get('discount_amount')
        min_purchase_amount = request.POST.get('min_purchase_amount')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        usage_limit = request.POST.get('usage_limit')
        
        if code and discount_amount and min_purchase_amount and start_date and end_date and usage_limit:
            Coupon.objects.create(
                code=code,
                discount_amount=discount_amount,
                min_purchase_amount=min_purchase_amount,
                valid_from=start_date,
                valid_to=end_date,
                usage_limit=usage_limit
            )
            messages.success(request, "Coupon added successfully!")
        else:
            messages.error(request, "Failed to add coupon. Please ensure all fields are filled.")
        
        return redirect('coupon:coupon_details')
    
    return render(request, 'admin/coupon.html')

@never_cache
def delete_coupon(request,coupon_id):
    code=Coupon.objects.get(coupon_id=coupon_id)
    code.delete()


    return redirect('coupon:coupon_details')
    
