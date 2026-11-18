import io
import os
from PIL import Image, ImageOps
from django.core.files.base import ContentFile


def compress_to_webp(image_field, max_dimension=1600, quality=80):
    """
    Görseli .webp formatına dönüştürür ve optimize eder.
    3-5 MB'lık yüksek çözünürlüklü görselleri kalite kaybı olmadan KB seviyelerine indirir.

    :param image_field: Modeldeki ImageField alanı (UploadedFile veya FieldFile)
    :param max_dimension: Maksimum genişlik / yükseklik piksel değeri (varsayılan 1600px)
    :param quality: WebP kalite oranı (0-100, varsayılan 80)
    :return: ContentFile (.webp) veya orijinal dosya
    """
    if not image_field:
        return image_field

    try:
        # Dosya göstericisini başa sar
        if hasattr(image_field, 'seek'):
            image_field.seek(0)

        # Görseli aç
        img = Image.open(image_field)

        # Mobil / kamera çekimlerindeki EXIF yönünü otomatik düzelt (yan/ters dönmeyi engeller)
        img = ImageOps.exif_transpose(img)

        # Şeffaflık (alpha) kontrolü ve renk modu dönüşümü
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            img = img.convert('RGBA')
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # En / boy oranını koruyarak max_dimension sınırına küçült
        if img.width > max_dimension or img.height > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        # WebP olarak belleğe optimize edilmiş kaydet
        output = io.BytesIO()
        img.save(output, format='WEBP', quality=quality, optimize=True)
        output.seek(0)

        # Dosya adının uzantısını .webp yap
        file_name = os.path.basename(image_field.name)
        base_name, _ = os.path.splitext(file_name)
        webp_filename = f"{base_name}.webp"

        return ContentFile(output.getvalue(), name=webp_filename)

    except Exception as e:
        # Herhangi bir beklenmeyen durumda orijinal dosyayı koru
        return image_field
