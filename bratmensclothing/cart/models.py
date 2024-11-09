from django.db import models
from accounts.models import Users
from products.models import VariantSize


class Cart(models.Model):
    cart_id = models.AutoField(primary_key=True)  
    user=models.ForeignKey(Users,on_delete=models.CASCADE,related_name="carts")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

class CartItem(models.Model):
    cartitem_id = models.AutoField(primary_key=True)
    cart =models.ForeignKey(Cart,on_delete=models.CASCADE,related_name="items")
    variant=models.ForeignKey(VariantSize,on_delete=models.CASCADE)
    quantity=models.PositiveBigIntegerField(default=0)


    @property
    def item_total(self):
        # return self.quantity * self.variant.price
        return self.quantity * self.variant.product.price
    
    def __str__(self):
        return f"{self.quantity} x {self.variant} in {self.cart}"