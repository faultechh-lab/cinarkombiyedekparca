import io
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Product


class ImageCompressionTest(TestCase):
    def setUp(self):
        media = TemporaryDirectory()
        self.addCleanup(media.cleanup)
        self.enterContext(self.settings(MEDIA_ROOT=media.name))

        # 3000x2000 boyutlarında yaklaşık 2.5 - 3 MB'lık test görseli oluştur
        img = Image.new('RGB', (3000, 2000), color=(100, 150, 200))
        draw = ImageDraw.Draw(img)
        for i in range(0, 3000, 15):
            draw.line([(i, 0), (3000 - i, 2000)], fill=(i % 255, (i * 3) % 255, 120), width=3)

        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=95)
        self.large_jpeg_bytes = buf.getvalue()
        self.original_size_mb = len(self.large_jpeg_bytes) / (1024 * 1024)

    def test_category_image_compressed_to_webp(self):
        uploaded = SimpleUploadedFile(
            name='test_category_photo.jpg',
            content=self.large_jpeg_bytes,
            content_type='image/jpeg'
        )

        category = Category.objects.create(name='Kombi Kartları', image=uploaded)
        self.assertTrue(category.image.name.endswith('.webp'))
        compressed_size_kb = category.image.size / 1024
        print(f"\n[Kategori Testi] Orijinal: {self.original_size_mb:.2f} MB -> Sıkıştırılmış: {compressed_size_kb:.2f} KB (.webp)")
        self.assertLess(compressed_size_kb, 500)

        with Image.open(category.image.path) as img:
            self.assertEqual(img.format, 'WEBP')
            self.assertLessEqual(max(img.width, img.height), 1600)

        category.delete()

    def test_product_image_compressed_to_webp(self):
        category = Category.objects.create(name='Sensörler')
        uploaded = SimpleUploadedFile(
            name='buyuk_urun_resmi.png',
            content=self.large_jpeg_bytes,
            content_type='image/png'
        )

        product = Product.objects.create(
            name='NTC Sıcaklık Sensörü',
            sku='NTC-001',
            category=category,
            image=uploaded
        )

        self.assertTrue(product.image.name.endswith('.webp'))
        compressed_size_kb = product.image.size / 1024
        print(f"[Ürün Testi] Orijinal: {self.original_size_mb:.2f} MB -> Sıkıştırılmış: {compressed_size_kb:.2f} KB (.webp)")
        self.assertLess(compressed_size_kb, 500)

        with Image.open(product.image.path) as img:
            self.assertEqual(img.format, 'WEBP')
            self.assertLessEqual(max(img.width, img.height), 1600)

        product.delete()
        category.delete()


class ProductAPICRUDTest(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            email='catalog-test@example.com', password='catalog-test-password!'
        )
        self.client.force_authenticate(self.user)
        self.cat1 = Category.objects.create(name='Elektronik Kartlar', description='Kombi anakartları')
        self.cat2 = Category.objects.create(name='Pompalar', description='Sirkülasyon pompaları')

        self.prod1 = Product.objects.create(
            name='ECA Proteus Plus Kart',
            sku='ECA-001',
            in_stock=True,
            category=self.cat1
        )
        self.prod2 = Product.objects.create(
            name='Demirdöküm Nitron Pompa',
            sku='DMD-002',
            category=self.cat2
        )

    def test_category_crud(self):
        # LIST
        res = self.client.get('/api/categories/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

        # CREATE
        res = self.client.post('/api/categories/', {'name': 'Fan Motorları', 'description': 'Hava akış fanları'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        new_cat_id = res.data['id']

        # RETRIEVE
        res = self.client.get(f'/api/categories/{new_cat_id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Fan Motorları')

        # UPDATE (PUT)
        res = self.client.put(f'/api/categories/{new_cat_id}/', {'name': 'Fan Motorları (Revize)', 'description': 'Tüm modeller'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Fan Motorları (Revize)')

        res = self.client.patch(f'/api/categories/{new_cat_id}/', {'description': 'Fan grupları'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['description'], 'Fan grupları')

        # DELETE
        res = self.client.delete(f'/api/categories/{new_cat_id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.filter(id=new_cat_id).count(), 0)

    def test_product_crud(self):
        # LIST
        res = self.client.get('/api/products/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

        # CREATE
        payload = {
            'name': 'Vaillant VUW Sensör',
            'sku': 'VAI-101',
            'category': self.cat1.id,
            'description': 'Orijinal NTC sensör'
        }
        res = self.client.post('/api/products/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        new_prod_id = res.data['id']
        self.assertFalse(res.data['in_stock'])
        self.assertNotIn('stock', res.data)

        # RETRIEVE
        res = self.client.get(f'/api/products/{new_prod_id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['sku'], 'VAI-101')
        self.assertEqual(res.data['category']['name'], 'Elektronik Kartlar')

        # PARTIAL UPDATE (PATCH)
        res = self.client.patch(f'/api/products/{new_prod_id}/', {'in_stock': True})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['in_stock'])

        res = self.client.put(f'/api/products/{new_prod_id}/', {
            **payload, 'name': 'Vaillant VUW Sıcaklık Sensörü', 'in_stock': False
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['in_stock'])

        # FILTER by category
        res = self.client.get(f'/api/products/?category={self.cat2.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual([product['sku'] for product in res.data], ['DMD-002'])

        # CUSTOM ACTION: out_of_stock
        res = self.client.get('/api/products/out_of_stock/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual({product['sku'] for product in res.data}, {'DMD-002', 'VAI-101'})

        # DELETE
        res = self.client.delete(f'/api/products/{new_prod_id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.filter(id=new_prod_id).count(), 0)

    def test_public_reads_and_superuser_only_writes(self):
        paths = [
            ('/api/categories/', f'/api/categories/{self.cat1.pk}/'),
            ('/api/products/', f'/api/products/{self.prod1.pk}/'),
        ]
        staff = get_user_model().objects.create_user(
            email='staff@example.com', password='catalog-test-password!', is_staff=True
        )
        for user in (None, staff):
            self.client.force_authenticate(user=user)
            for collection, item in paths:
                with self.subTest(user=user, collection=collection):
                    self.assertEqual(self.client.get(collection).status_code, 200)
                    self.assertEqual(self.client.post(collection, {}).status_code, 403)
                    self.assertEqual(self.client.put(item, {}).status_code, 403)
                    self.assertEqual(self.client.patch(item, {}).status_code, 403)
                    self.assertEqual(self.client.delete(item).status_code, 403)

    def test_invalid_category_filter_does_not_raise_server_error(self):
        response = self.client.get('/api/products/', {'category': 'not-a-number'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('category', response.data)

    def test_image_can_be_uploaded_and_removed_through_both_endpoints(self):
        media = TemporaryDirectory()
        self.addCleanup(media.cleanup)
        self.enterContext(self.settings(MEDIA_ROOT=media.name))
        image_bytes = io.BytesIO()
        Image.new('RGB', (24, 24), color='navy').save(image_bytes, format='PNG')
        paths = [
            f'/api/categories/{self.cat1.pk}/',
            f'/api/products/{self.prod1.pk}/',
        ]
        for path in paths:
            with self.subTest(path=path):
                file = SimpleUploadedFile('test.png', image_bytes.getvalue(), 'image/png')
                response = self.client.patch(path, {'image': file}, format='multipart')
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.data['image'].endswith('.webp'))
                response = self.client.patch(path, {'image': None}, format='json')
                self.assertEqual(response.status_code, 200)
                self.assertIsNone(response.data['image'])

    def test_category_count_and_cascade(self):
        response = self.client.get(f'/api/categories/{self.cat1.pk}/')
        self.assertEqual(response.data['product_count'], 1)
        self.assertEqual(len(response.data['products']), 1)
        self.assertEqual(self.client.delete(f'/api/categories/{self.cat1.pk}/').status_code, 204)
        self.assertFalse(Product.objects.filter(pk=self.prod1.pk).exists())
        self.assertTrue(Product.objects.filter(pk=self.prod2.pk).exists())
