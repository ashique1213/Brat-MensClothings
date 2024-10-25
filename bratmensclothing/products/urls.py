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

app_name = 'products'

urlpatterns = [
    path('addbrands/',views.add_brands,name='add_brands'),
    path('viewbrands/', views.view_brands, name='view_brands'),
    path('edit-brands/<int:brand_id>', views.edit_brands, name='edit_brands'),
    path('brand/soft-delete/<int:brand_id>/', views.soft_delete_brand, name='soft_delete_brand'),
    path('brand/restore/<int:brand_id>/', views.restore_brand, name='restore_brand'),
    path('addcategory/',views.add_category,name='add_category'),
    path('viewcategory/', views.view_category, name='view_category'),
    path('edit-category/<int:category_id>', views.edit_category, name='edit_category'),
    path('category/soft-delete/<int:category_id>/', views.soft_delete_category, name='soft_delete_category'),
    path('category/restore/<int:category_id>/', views.restore_category, name='restore_category'),
    path('addproduct/',views.add_products,name='add_products'),
    path('viewproducts/', views.view_products, name='view_products'),
    path('edit-product/<int:product_id>', views.edit_product, name='edit_product'),
    path('products/soft-delete/<int:product_id>/', views.soft_delete_product, name='soft_delete_product'),
    path('products/restore/<int:product_id>/', views.restore_product, name='restore_product'),
    path('addvariants/<int:product_id>/', views.add_variants, name='add_variants'),
    path('variants/<int:product_id>/', views.view_variants, name='view_variants'),
    path('edit-variants/<int:product_id>/', views.edit_variants, name='edit_variants'),
    path('delete-variants/<int:product_id>/', views.delete_variants, name='delete_variants'),

    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
