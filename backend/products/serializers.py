from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    def get_product_count(self, category):
        if hasattr(category, 'total_products'):
            return category.total_products
        return category.products.count()

    class Meta:
        model = Category
        fields = [
            'id',
            'slug',
            'name',
            'image',
            'description',
            'product_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True, allow_null=True)

    def validate_sku(self, value):
        return value or None

    class Meta:
        model = Product
        fields = [
            'id',
            'slug',
            'name',
            'sku',
            'description',
            'category',
            'category_name',
            'category_slug',
            'in_stock',
            'image',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ProductDetailSerializer(ProductSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['category_id']


class CategoryDetailSerializer(CategorySerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ['products']
