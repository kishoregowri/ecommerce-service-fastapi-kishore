# shop/models.py
from decimal import Decimal
from django.db import models

class Product(models.Model):
    sku = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=12, decimal_places=2)  # INR/USD etc.
    currency = models.CharField(max_length=8, default="INR")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"{self.sku} - {self.name}"

class Cart(models.Model):
    # We’ll scope carts by a header-provided user reference (no auth DB needed)
    user_ref = models.CharField(max_length=128, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sku = models.CharField(max_length=64, db_index=True)
    qty = models.PositiveIntegerField()

    class Meta:
        unique_together = ("cart","sku")
