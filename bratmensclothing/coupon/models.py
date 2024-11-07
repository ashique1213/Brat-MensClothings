from django.db import models
from accounts.models import Users
from django.utils import timezone

class Coupon(models.Model):
    coupon_id = models.AutoField(primary_key=True)  
    code  =  models.CharField(max_length=30,unique=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    min_purchase_amount = models.DecimalField(max_digits=10,decimal_places=2)
    valid_from = models.DateField()
    valid_to = models.DateField()
    is_active = models.BooleanField(default=True)
    usage_limit = models.PositiveIntegerField(default=1)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Coupon {self.code} ({self.discount_amount})"

    def is_valid(self):
        now = timezone.now().date()
        return self.is_active and self.valid_from <= now <= self.valid_to


class CouponUser(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE) 
    status = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}-{self.coupon.code}"

    def can_use(self):
        """Check if the coupon can still be used by the user (hasn't been used yet)."""
        return not self.used