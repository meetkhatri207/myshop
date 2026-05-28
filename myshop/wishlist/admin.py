from django.contrib import admin
from .models import Wishlist

class wishlistAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'product',
        'created_at'
    )

# Register your models here.
admin.site.register(Wishlist, wishlistAdmin)

