from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from .managers import UserManager

class User(AbstractUser):
    username = None
    email = models.EmailField(_('email adresi'), unique=True)
    first_name = models.CharField(_('ad'), max_length=150, blank=True)
    last_name = models.CharField(_('soyad'), max_length=150, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _('Kullanıcı')
        verbose_name_plural = _('Kullanıcılar')

    def __str__(self):
        return self.email
