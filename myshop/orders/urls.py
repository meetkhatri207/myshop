from django.urls import path
from . import views

urlpatterns = [
    path('apply-coupon/', views.apply_coupon),
    path('remove-coupon/', views.remove_coupon),
    path('create-order/', views.create_order, name='create_order'),
    path('shipping-address/', views.shipping_address),
    path('my-orders/', views.my_orders),
    path('detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('invoice/<int:order_id>/', views.invoice_pdf),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('payment/verify/', views.verify_payment, name='verify_payment'),
    path(
        'payment/success/<int:order_id>/',
        views.payment_success,
        name='payment_success',
    ),
    path(
        'payment/failed/',
        views.payment_failed,
        name='payment_failed',
    ),
    path(
        'payment/',
        views.payment_page,
        name='payment_page',
    ),
    path('<int:order_id>/', views.order_detail),
]