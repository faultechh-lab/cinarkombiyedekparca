from rest_framework import filters, permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.db.models import Count

from .models import Category, Product
from .serializers import (
    CategorySerializer,
    CategoryDetailSerializer,
    ProductSerializer,
    ProductDetailSerializer,
)


class PublicCatalogPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or (
            request.user.is_authenticated
            and request.user.is_active
            and request.user.is_superuser
        )


class CategoryViewSet(viewsets.ModelViewSet):
    """
    Kategori CRUD İşlemleri:
    - GET    /api/categories/         -> Tüm kategorileri listele
    - POST   /api/categories/         -> Yeni kategori oluştur
    - GET    /api/categories/{id}/    -> Kategori detayı ve ürünlerini getir
    - PUT    /api/categories/{id}/    -> Kategoriyi tamamen güncelle
    - PATCH  /api/categories/{id}/    -> Kategoriyi kısmen güncelle
    - DELETE /api/categories/{id}/    -> Kategoriyi sil
    """
    queryset = Category.objects.annotate(total_products=Count('products'))
    serializer_class = CategorySerializer
    permission_classes = [PublicCatalogPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        slug = self.request.query_params.get('slug')
        return queryset.filter(slug=slug) if slug else queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CategoryDetailSerializer
        return CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    Ürün CRUD İşlemleri:
    - GET    /api/products/           -> Ürünleri listele (arama, sıralama ve kategoriye göre filtreleme destekler)
    - POST   /api/products/           -> Yeni ürün oluştur (görsel otomatik .webp olarak sıkıştırılır)
    - GET    /api/products/{id}/      -> Ürün detayını getir
    - PUT    /api/products/{id}/      -> Ürünü tamamen güncelle
    - PATCH  /api/products/{id}/      -> Ürünü kısmen güncelle
    - DELETE /api/products/{id}/      -> Ürünü sil
    """
    serializer_class = ProductSerializer
    permission_classes = [PublicCatalogPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'sku', 'description', 'category__name']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Product.objects.select_related('category').all()
        slug = self.request.query_params.get('slug')
        if slug:
            queryset = queryset.filter(slug=slug)

        # ?category=1 (Kategoriye göre filtreleme)
        category_id = self.request.query_params.get('category')
        if category_id:
            try:
                category_id = serializers.IntegerField(min_value=1, max_value=2**63 - 1).run_validation(category_id)
            except ValidationError as error:
                raise ValidationError({"category": "Geçerli bir kategori kimliği gönderin."}) from error
            queryset = queryset.filter(category_id=category_id)

        # ?in_stock=true veya ?in_stock=false (Stok durumuna göre filtreleme)
        in_stock_param = self.request.query_params.get('in_stock')
        if in_stock_param is not None:
            if in_stock_param.lower() in ('true', '1'):
                queryset = queryset.filter(in_stock=True)
            elif in_stock_param.lower() in ('false', '0'):
                queryset = queryset.filter(in_stock=False)

        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer

    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """Mevcut olmayan ürünleri listele."""
        products = self.get_queryset().filter(in_stock=False)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
