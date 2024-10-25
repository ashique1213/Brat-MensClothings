from django.contrib.auth.models import AbstractUser
from django.db import models

class Users(AbstractUser):
    # You can add any extra fields here
    userid = models.AutoField(primary_key=True)  # Optional, as the `id` field already exists
    phone_number = models.CharField(max_length=15, null=True)
    profile = models.ImageField(upload_to='profiles/', null=True, blank=True)
    address = models.TextField(null=True)
    # isBlocked = models.BooleanField(default=False)  # Custom field
    # created_at = models.DateTimeField(auto_now_add=True)  # Custom field

    def __str__(self):
        return self.username
