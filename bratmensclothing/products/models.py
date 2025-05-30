from django.db import models
from django.contrib.postgres.fields import ArrayField
from cloudinary.models import CloudinaryField
from accounts.models import Users


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


class ProductDetails(models.Model):
    product_id = models.AutoField(primary_key=True)  
    product_name = models.CharField(max_length=100)
    description = models.TextField()
    # image1 = models.ImageField(upload_to='products/', null=False, blank=False)
    image1 = CloudinaryField('image', folder='home/products',null=True, blank=True)
    # image2 = models.ImageField(upload_to='products/', null=False, blank=False) 
    image2 = CloudinaryField('image', folder='home/products',null=True, blank=True)
    # image3 = models.ImageField(upload_to='products/', null=False, blank=False)  
    image3 = CloudinaryField('image', folder='home/products',null=True, blank=True)
    # image4 = models.ImageField(upload_to='products/', null=False, blank=False)  
    image4 = CloudinaryField('image', folder='home/products',null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    color = models.CharField(max_length=30) 
    occasion = models.CharField(max_length=30) 
    fit = models.CharField(max_length=30)
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE,related_name='products')
    category = models.ManyToManyField('Category', related_name='product_list', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=True)  
    
    
    def __str__(self):
        return self.product_name

class VariantSize(models.Model):  
    variant_id = models.AutoField(primary_key=True)  
    size = models.CharField(max_length=10)
    qty = models.IntegerField()
    is_deleted = models.BooleanField(default=False)
    product = models.ForeignKey(ProductDetails, related_name='variants', on_delete=models.CASCADE)

    def __str__(self):
        return f"Variant of {self.product.product_name} - Size: {self.size}"
    
    class Meta:
        ordering = ['size'] 
    
    
    


class Review(models.Model):
    product = models.ForeignKey(ProductDetails,related_name='Rating', on_delete=models.CASCADE)
    user = models.ForeignKey(Users,related_name='Users', on_delete=models.CASCADE)
    rating = models.IntegerField()
    review = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Review for {self.product.name} by {self.user.username}'

    class Meta:
        ordering = ['-created_at']