from django.contrib import admin
from .models import Order, OrderItem, Coupon, ShippingAddress

class OrderAdmin(admin.ModelAdmin):
    list_display = (
    'id',
    'user',
    'total_price',
    'payment_status',
    'status',
    'created_at'
)

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(Coupon)
admin.site.register(ShippingAddress)




