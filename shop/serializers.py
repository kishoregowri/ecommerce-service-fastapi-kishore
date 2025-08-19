# shop/serializers.py
from decimal import Decimal
from rest_framework import serializers
from .models import Product, CartItem, Cart
from .utils import cart_signature

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id","sku","name","price","currency","created_at"]
        read_only_fields = ["id","created_at"]

class CartItemWriteSerializer(serializers.Serializer):
    sku = serializers.CharField(max_length=64)
    qty = serializers.IntegerField(min_value=0)  # 0 allowed for PUT set-to-0

class CartItemReadSerializer(serializers.Serializer):
    sku = serializers.CharField()
    name = serializers.CharField()
    qty = serializers.IntegerField()
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    line_total = serializers.DecimalField(max_digits=14, decimal_places=2)

class CartViewSerializer(serializers.Serializer):
    items = CartItemReadSerializer(many=True)
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2)
    currency = serializers.CharField()
    normalization = serializers.CharField()
    signature = serializers.CharField()
