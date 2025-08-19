# shop/views.py
from decimal import Decimal
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from .models import Product, Cart, CartItem
from .serializers import (
    ProductSerializer, CartItemWriteSerializer, CartViewSerializer, CartItemReadSerializer
)
from .permissions import IsAdminOrReadOnly, IsUserRole
from .utils import cart_signature

class ProductViewSet(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    queryset = Product.objects.all().order_by("id")
    serializer_class = ProductSerializer
    filter_backends = [SearchFilter]
    search_fields = ["name","sku"]
    permission_classes = [IsAdminOrReadOnly]

class CartView(APIView):
    permission_classes = [IsUserRole]

    def _get_or_create_cart(self, request) -> Cart:
        user_ref = request.user.user_id
        cart, _ = Cart.objects.get_or_create(user_ref=user_ref)
        return cart

    def get(self, request):
        cart = self._get_or_create_cart(request)
        items_qs = (CartItem.objects
                    .filter(cart=cart)
                    .select_related("product")
                    .order_by("sku"))
        items = []
        for it in items_qs:
            line_total = (it.product.price * it.qty).quantize(Decimal("0.01"))
            items.append({
                "sku": it.sku,
                "name": it.product.name,
                "qty": it.qty,
                "unit_price": it.product.price,
                "line_total": line_total,
            })

        normalization, signature = cart_signature(
            [{"sku": i["sku"], "qty": i["qty"]} for i in items]
        )
        subtotal = sum((i["line_total"] for i in items), Decimal("0"))
        data = {
            "items": items,
            "subtotal": subtotal,
            "currency": items_qs[0].product.currency if items_qs else "INR",
            "normalization": normalization,
            "signature": signature,
        }
        return Response(CartViewSerializer(data).data)

class CartItemsView(APIView):
    """
    POST /cart/items    { sku, qty }  -> add qty (increment)
    PUT  /cart/items/:sku { qty }     -> set qty (idempotent)
    DELETE /cart/items/:sku           -> remove
    """
    permission_classes = [IsUserRole]

    def _get_cart(self, request) -> Cart:
        return Cart.objects.get_or_create(user_ref=request.user.user_id)[0]

    @transaction.atomic
    def post(self, request):
        ser = CartItemWriteSerializer(data=request.data); ser.is_valid(raise_exception=True)
        sku = ser.validated_data["sku"]
        qty = ser.validated_data["qty"]
        if qty <= 0:
            return Response({"detail":"qty must be > 0 for POST."},
                            status=status.HTTP_400_BAD_REQUEST)
        product = get_object_or_404(Product, sku=sku)
        cart = self._get_cart(request)
        item, created = CartItem.objects.select_for_update().get_or_create(
            cart=cart, sku=sku, defaults={"product": product, "qty": 0}
        )
        item.qty += qty
        item.product = product
        item.save()
        return Response({"detail":"added","sku":sku,"qty":item.qty}, status=201)

    @transaction.atomic
    def put(self, request, sku):
        ser = CartItemWriteSerializer(data=request.data); ser.is_valid(raise_exception=True)
        qty = ser.validated_data["qty"]
        product = get_object_or_404(Product, sku=sku)
        cart = self._get_cart(request)
        try:
            item = CartItem.objects.select_for_update().get(cart=cart, sku=sku)
        except CartItem.DoesNotExist:
            if qty == 0:
                return Response({"detail":"no-op"}, status=200)
            item = CartItem(cart=cart, product=product, sku=sku, qty=0)
        item.product = product
        item.qty = qty
        if item.qty <= 0:
            item.delete()
            return Response({"detail":"deleted"}, status=200)
        item.save()
        return Response({"detail":"set","sku":sku,"qty":item.qty}, status=200)

    @transaction.atomic
    def delete(self, request, sku):
        cart = self._get_cart(request)
        deleted, _ = CartItem.objects.filter(cart=cart, sku=sku).delete()
        if deleted:
            return Response(status=204)
        return Response({"detail":"not found"}, status=404)
