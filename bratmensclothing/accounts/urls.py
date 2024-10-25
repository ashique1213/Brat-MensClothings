"""
URL configuration for bratmensclothing project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path,include
from . import views
# from .views import GoogleLogin

app_name = 'accounts'

urlpatterns = [
    path('signupuser/',views.signup_user,name='signup_user'),
    path('login/',views.login_user,name='login_user'),
    path('',views.home_user,name='home_user'),    
    path('adminlogin/',views.admin_login,name='admin_login'),    
    path('adminlogout/',views.admin_logout,name='admin_logout'),  
    path('otp-verify/', views.otp_verify, name='otp_verify'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('logoutuser/', views.logout_user, name='logout_user'),
]
 