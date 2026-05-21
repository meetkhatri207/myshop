import razorpay
from django.shortcuts import get_object_or_404, render
from .models import Order, OrderItem, Coupon
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings


def payment_success(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    order.payment_status = True

    order.save()

    return render(request, 'orders/success.html', {
        'order': order
    })

def order_detail(request, order_id):

    order = Order.objects.get(id=order_id)

    items = OrderItem.objects.filter(
        order=order
    )

    return render(request, 'orders/detail.html', {
        'order': order,
        'items': items
    })

def apply_coupon(request):

    code = request.POST.get('code')

    try:

        coupon = Coupon.objects.get(
            code=code,
            active=True
        )

        request.session['coupon'] = {
            'code': coupon.code,
            'discount': coupon.discount
        }

    except Coupon.DoesNotExist:

        return HttpResponse(
            'Invalid Coupon'
        )

    return redirect('/cart/')

def remove_coupon(request):
    if 'coupon' in request.session:
        del request.session['coupon']

    return redirect('/cart/')

@login_required
def payment_page(request, order_id):

    order = Order.objects.get(
        id=order_id
    )

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    payment = client.order.create({

        'amount': int(
            order.total_price * 100
        ),

        'currency': 'INR',

        'payment_capture': '1'
    })

    order.razorpay_order_id = payment['id']

    order.save()

    return render(
        request,
        'orders/payment.html',
        {
            'order': order,
            'payment': payment,
            'razorpay_key': settings.RAZORPAY_KEY_ID
        }
    )

@login_required
def my_orders(request):

    orders = Order.objects.filter(
        user=request.user
    ).order_by('-id')

    print(orders)

    return render(request, 'orders/my_orders.html', {
        orders : orders
    })

@login_required
def order_detail(request, order_id):

    order = Order.objects.get(
        id=order_id,
        user=request.user
    )

    order_items = OrderItem.objects.filter(
        order=order
    )

    return render(
        request, 'orders/detail.html', {
            'order': order,
            'order_items': order_detail
        }
    )