from django.db import models
from products.models import VariantSize
from accounts.models import Users

class Wishlist(models.Model):
    user=models.ForeignKey(Users,on_delete=models.CASCADE,related_name="user")
    product = models.ForeignKey(VariantSize, on_delete=models.CASCADE,related_name="products")
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s wishlist item: {self.product.name}"
