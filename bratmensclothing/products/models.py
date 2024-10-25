from django.db import models
from django.contrib.postgres.fields import ArrayField

class Category(models.Model):
    CATEGORY_CHOICES = [
        ('Tshirt', 'T-shirt'),
        ('Shirt', 'Shirt'),
        ('Jeans', 'Jeans'),
        ('Pants', 'Pants'),
    ]

    category_id = models.AutoField(primary_key=True)  
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)  
    category_type = models.CharField(max_length=50)   
    created_date = models.DateTimeField(auto_now_add=True) 
    updated_date = models.DateTimeField(auto_now=True) 
    is_deleted = models.BooleanField(default=False)
      

    def __str__(self):
        return self.category 
    
class Brand(models.Model):
    brand_id = models.AutoField(primary_key=True)  
    brandname = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)


    def __str__(self):
        return self.brandname


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)  
    product_name = models.CharField(max_length=100)
    description = models.TextField()
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    category = models.ManyToManyField(Category, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=True)

    def __str__(self):
        return self.product_name



class Variant(models.Model):  
    variant_id = models.AutoField(primary_key=True)  
    image1 = models.ImageField(upload_to='products/', null=False, blank=False)
    image2 = models.ImageField(upload_to='products/', null=False, blank=False) 
    image3 = models.ImageField(upload_to='products/', null=False, blank=False)  
    image4 = models.ImageField(upload_to='products/', null=False, blank=False)  
    size = ArrayField(models.CharField(max_length=10), blank=True, default=list)
    # color = ArrayField(models.CharField(max_length=10), blank=True, default=list)
    color = models.CharField(max_length=30) 
    occation = models.CharField(max_length=30) 
    fit = models.CharField(max_length=30)
    qty = models.IntegerField()
    price = models.IntegerField(null=True, blank=True)
    status = models.BooleanField(default=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)  

    def __str__(self):
        return f"Variant of {self.product} - Size: {self.size}, Color: {self.color}"



    
# class Review(models.Model):
#     product_id = models.ForeignKey(variant,on_delete=models.CASCADE)
#     user_id = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
#     review = models.TextField()
#     created_at = models.DateTimeField(default=timezone.now)
    