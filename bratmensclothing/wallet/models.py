from django.db import models
from accounts.models import Users
# Create your models here.

class Wallet(models.Model):
    wallet_id = models.AutoField(primary_key=True)  
    user_id = models.ForeignKey(Users,on_delete=models.CASCADE)
    balance = models.DecimalField(decimal_places=2, default=0.00,max_digits=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Transaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)  
    wallet_id = models.ForeignKey(Wallet,on_delete=models.CASCADE)
    details = models.CharField( max_length=256)
    amount = models.IntegerField(null=True,blank=True) 
    transaction_type = models.CharField(max_length=50) 
    created_at = models.DateTimeField(auto_now_add=True)
    