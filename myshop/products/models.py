from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.IntegerField()
    description = models.TextField()
    stock = models.IntegerField()
    image = models.ImageField(upload_to='products/', null=True, blank=True, default='default/no-image.png')
    category = models.ForeignKey(
    Category,
    on_delete=models.CASCADE,
    null=True,
    blank=True
)

    def __str__(self):
        return self.name

