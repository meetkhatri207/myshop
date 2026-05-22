from django.db import models
from django.contrib.auth.models import User
from products.models import Product

class ShippingAddress(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    full_name = models.CharField(
        max_length=255
    )

    phone = models.CharField(
        max_length=20
    )

    address = models.TextField()

    city = models.CharField(
        max_length=100
    )

    state = models.CharField(
        max_length=100
    )

    pincode = models.CharField(
        max_length=20
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.full_name


class Order(models.Model):

    STATUS_CHOICES = [

    ('Pending', 'Pending'),

    ('Processing', 'Processing'),

    ('Shipped', 'Shipped'),

    ('Delivered', 'Delivered'),

    ('Cancelled', 'Cancelled')

]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    payment_status = models.BooleanField(default=False)

    razorpay_order_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    payment_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    status = models.CharField(

    max_length=20,

    choices=STATUS_CHOICES,

    default='Pending'
    )    

    shipping_address = models.ForeignKey(

    ShippingAddress,

    on_delete=models.SET_NULL,

    null=True,

    blank=True
)

    def __str__(self):

        return self.user.username


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.IntegerField(default=1)

    price = models.IntegerField(null=True)

    def __str__(self):

        return self.product.name

class Coupon(models.Model):
    code = models.CharField(max_length=50,unique=True)
    discount = models.IntegerField(null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


