from django.shortcuts import render

from orders.models import Order
from products.models import Product
from django.contrib.auth.models import User

from django.db.models import Sum


def dashboard(request):

    total_orders = Order.objects.count()

    total_users = User.objects.count()

    total_products = Product.objects.count()

    revenue = Order.objects.aggregate(
        Sum('total_price')
    )['total_price__sum'] or 0

    revenue = "{:,.2f}".format(revenue)

    if revenue is None:
        revenue = 0

    latest_orders = Order.objects.order_by(
        '-id'
    )[:5]

    return render(
        request,
        'dashboard/index.html',
        {
            'total_orders': total_orders,
            'total_users': total_users,
            'total_products': total_products,
            'revenue': revenue,
            'latest_orders': latest_orders
        }
    )