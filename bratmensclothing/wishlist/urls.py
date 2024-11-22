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

app_name = 'wishlist'

urlpatterns = [
   
    path('wishlist/', views.view_wishlist, name='viewwishlist'),  
    path('add_to_wishlist/<int:product_id>',views.add_to_wishlist,name='add_to_wishlist'),
    path('remove_wishlist/<int:variant_id>',views.remove_wishlist,name='remove_wishlist'),
    path('clear_wishlist/',views.clear_wishlist,name='clear_wishlist')
    
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
