from django.contrib.auth.models import AbstractUser
from django.db import models

class Users(AbstractUser):
    userid = models.AutoField(primary_key=True)  # Optional, as the `id` field already exists
    phone_number = models.CharField(max_length=15, null=True)
    profile = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    def __str__(self):
        return self.username
