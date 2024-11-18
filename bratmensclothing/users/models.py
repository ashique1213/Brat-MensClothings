from django.db import models
from accounts.models import Users


class Address(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='addresses')
    address = models.CharField(max_length=255)
    street = models.CharField(max_length=100)
    landmark = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    pincode = models.IntegerField()
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    status=models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.street}, {self.city}, {self.state} - {self.district}"