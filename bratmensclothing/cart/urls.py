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

app_name = 'cart'

urlpatterns = [
   
    path('cart/', views.view_cart, name='viewcart'),  
    path('cart/add/<int:variant_id>/', views.add_to_cart, name='addtocart'),  
    path('cart/delete/<int:cartitem_id>/', views.delete_item, name='delete_item'),  
    path('update/<int:cart_item_id>/',views.update_cart_item, name='update_cart_item'),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
