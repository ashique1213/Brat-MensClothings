from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField


class Users(AbstractUser):
    userid = models.AutoField(primary_key=True) 
    phone_number = models.CharField(max_length=15, null=True)
    # profile = models.ImageField(upload_to='profiles/', null=True, blank=True)
    profile = CloudinaryField('image', folder='home/profile_pics',null=True, blank=True)
    
    def __str__(self):
        return self.username
