from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
# from accounts.models  import 
from django.contrib.auth.decorators import login_required,user_passes_test
from django.views.decorators.cache import never_cache



def is_staff(user):
    return user.is_staff


@login_required(login_url='accounts:admin_login')
@never_cache
@user_passes_test(is_staff,'accounts:admin_login')
def admin_dashboard(request):
    if not request.user.is_authenticated or not request.user.is_superuser: 
        return redirect('accounts:admin_login')
    
    return render(request, 'admin/dashboard.html')