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

app_name = 'coupon'

urlpatterns = [
   
    path('coupon_details/', views.coupon_details, name='coupon_details'),  
    path('add_coupon/', views.add_coupon, name='add_coupon'),  
    path('edit_coupon/<int:coupon_id>', views.edit_coupon, name='edit_coupon'),  
    path('delete_coupon/<int:coupon_id>', views.delete_coupon, name='delete_coupon'), 
    path('soft-delete-coupon/<int:coupon_id>/', views.soft_delete_coupon, name='soft_delete_coupon'),
    path('restore-coupon/<int:coupon_id>/', views.restore_coupon, name='restore_coupon'), 

    path('apply_coupon/',views.apply_coupon,name='apply_coupon'),
    path('remove_coupon/<int:id>',views.remove_coupon,name='remove_coupon')


    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
