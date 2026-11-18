from uuid import uuid4

from django.db import models
from django.utils.text import slugify
from .utils import compress_to_webp


def new_slug(name):
    base = slugify(name.replace("ı", "i").replace("İ", "I"))[:200]
    return f"{base or 'kayit'}-{uuid4().hex[:12]}"


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Kategori Adı")
    slug = models.SlugField(max_length=220, unique=True, editable=False)
    image = models.ImageField(upload_to='categories/images/', null=True, blank=True, verbose_name="Kategori Görseli")
    description = models.TextField(null=True, blank=True, verbose_name="Açıklama")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")

    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategoriler"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = new_slug(self.name)
        if self.image:
            is_new_image = False
            if not self.pk:
                is_new_image = True
            else:
                old_instance = Category.objects.filter(pk=self.pk).only('image').first()
                if old_instance and old_instance.image != self.image:
                    is_new_image = True

            if is_new_image:
                self.image = compress_to_webp(self.image)

        super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Ürün Adı")
    slug = models.SlugField(max_length=220, unique=True, editable=False)
    sku = models.CharField(max_length=100, unique=True, verbose_name="Stok Kodu (SKU)")
    description = models.TextField(null=True, blank=True, verbose_name="Açıklama")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Kategori")
    in_stock = models.BooleanField(default=False, verbose_name="Stokta Var mı?")
    image = models.ImageField(upload_to='products/images/', null=True, blank=True, verbose_name="Ürün Görseli")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")

    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = new_slug(self.name)
        if self.image:
            is_new_image = False
            if not self.pk:
                is_new_image = True
            else:
                old_instance = Product.objects.filter(pk=self.pk).only('image').first()
                if old_instance and old_instance.image != self.image:
                    is_new_image = True

            if is_new_image:
                self.image = compress_to_webp(self.image)

        super().save(*args, **kwargs)
