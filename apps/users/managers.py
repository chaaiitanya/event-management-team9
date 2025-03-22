from django.contrib.auth.models import BaseUserManager
from apps.users import models

class MyAccountManager(BaseUserManager):
    def create_user(self, email, password):
        if not email:
            raise ValueError("Users must have an Emaill address")
        user  = self.model(
                email=self.normalize_email(email)
            )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(
                email=self.normalize_email(email),
                password=password,
            )
        user.is_admin = True
        user.is_staff=True
        user.is_superuser=True
        user.save(using=self._db)
        return user
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)