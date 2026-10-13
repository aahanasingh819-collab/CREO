from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class User(AbstractUser):
    class Role(models.TextChoices):
        CREATOR = 'CREATOR', 'Creator'
        BRAND = 'BRAND', 'Brand'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CREATOR, db_index=True)

    class Meta:
        constraints = [models.UniqueConstraint(Lower('email'), name='unique_user_email_ci'),
                       models.CheckConstraint(condition=models.Q(role__in=['CREATOR', 'BRAND']), name='valid_user_role')]
