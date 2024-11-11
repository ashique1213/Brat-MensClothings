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

app_name = 'order'

urlpatterns = [
   
    path('checkout/', views.checkout, name='checkout'),  
    path('add_address_checkout/<int:userid>', views.add_address_checkout, name='add_address_checkout'),  
    path('place-order/', views.place_order, name='place_order'),    
    path('verify-payment/', views.verify_payment, name='verify_payment'),  
    path('order_success/', views.order_success, name='order_success'),    
    path('view_orders/', views.view_orders, name='view_orders'),    
    path('manage_orders/<int:orderitem_id>', views.manage_orders, name='manage_orders'),    
    path('cancel_order/<int:orderitem_id>', views.cancel_order, name='cancel_order'),    
    path('order_details/',views.order_details,name='order_details'),
    path('return_order/<int:orderitem_id>',views.return_order,name='return_order'),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
