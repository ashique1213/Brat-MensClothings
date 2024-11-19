from django.db import models
from products.models import Brand,ProductDetails

class Product_Offers(models.Model):
    product = models.ForeignKey(ProductDetails,on_delete=models.CASCADE)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2)
    offer_name = models.CharField(null=True,blank=True)
    offer_details = models.TextField(null=True,blank=True)
    started_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Brand_Offers(models.Model):
    brand = models.ForeignKey(Brand,on_delete=models.CASCADE)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2)
    offer_name = models.CharField(null=True,blank=True)
    offer_details = models.TextField(null=True,blank=True)
    started_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)