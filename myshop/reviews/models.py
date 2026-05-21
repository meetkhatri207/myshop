from django.db import models
from django.contrib.auth.models import User
from products.models import Product


class Review(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    rating = models.IntegerField()

    comment = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.product.name