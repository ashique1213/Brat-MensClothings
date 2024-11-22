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

app_name = 'offer'

urlpatterns = [
   
    path('offer/', views.view_offer, name='view_offer'),  
    path('view_brand_offer/', views.view_brand_offer, name='view_brand_offer'),  
    path('add_brand_offer   /', views.add_brand_offer, name='add_brand_offer'),  
    path('edit_brand_offer/<int:offer_id>/', views.edit_brand_offer, name='edit_brand_offer'),


    path('view_product_offer/', views.view_product_offer, name='view_product_offer'),  
    path('add_product_offer/', views.add_product_offer, name='add_product_offer'), 
    path('edit_product_offer/<int:offer_id>/', views.edit_product_offer, name='edit_product_offer'),
 
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
