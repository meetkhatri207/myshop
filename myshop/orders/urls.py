from django.urls import path
from . import views

urlpatterns = [
#    path(
#     'payment-success/<int:order_id>/',
#     views.payment_success
# ),
path(
    'detail/<int:order_id>/',
    views.order_detail
),
path('apply-coupon/', views.apply_coupon),

path('remove-coupon/', views.remove_coupon),

path('create-order/', views.create_order, name='create_order'),

path(
    'payment/<int:order_id>/',
    views.payment_page,
    name='payment_page'
),
path('my-orders/', views.my_orders),
path('<int:order_id>/', views.order_detail),
path(
    'shipping-address/',
    views.shipping_address
),
path(
    'invoice/<int:order_id>/',
    views.invoice_pdf
),
]