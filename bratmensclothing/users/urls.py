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
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'userss'

urlpatterns = [
    path('404/',views.error,name='error'),
    path('view_user/',views.view_user,name='view_user'),
    path('block-user/<int:userid>',views.block_user,name='block_user'),
    path('unblock-user/<int:userid>',views.unblock_user,name='unblock_user'),
    path('categorydetails/',views.category_details,name='category_details'),
    path('productdetails/<int:product_id>/',views.product_details,name='product_details'),
    
    
    path('addprofile/<int:userid>',views.add_profile,name='addprofile'),
    path('deleteprofile/<int:userid>',views.delete_profile,name='deleteprofile'),
    path('accountdetails/<int:userid>',views.account_details,name='accountdetails'),
    path('accountdetails/edit_account_dtails/<int:userid>',views.edit_account_details,name='edit_account_dtails'),
    path('accountdetails/resetpassword/<int:userid>',views.reset_password,name='resetpassword'),
    
    path('addressdetails/<int:userid>',views.address_details,name='addressdetails'),
    path('addressdetails/addaddress/<int:userid>',views.add_address,name='addaddress'),
    path('addressdetails/editaddress/<int:id>',views.edit_address,name='editaddress'),
    path('removeaddress/<int:id>/', views.remove_address, name='removeaddress'),
    
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
]
if settings.DEBUG:  
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)