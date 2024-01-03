from django.contrib.auth.models import AbstractUser
from django.db import models


class Parcel(models.Model):
    parcel_number = models.CharField(max_length=50)

    def __str__(self):
        return self.parcel_number


