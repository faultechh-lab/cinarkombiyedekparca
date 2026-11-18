from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    """
    Email adresini benzersiz kimlik olarak kullanan özel kullanıcı yöneticisi.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Email adresi zorunludur.'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Süper kullanıcı is_staff=True olmalıdır.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Süper kullanıcı is_superuser=True olmalıdır.'))

        return self.create_user(email, password, **extra_fields)
