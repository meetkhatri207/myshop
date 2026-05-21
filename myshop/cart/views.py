from django.shortcuts import render, redirect, get_object_or_404
from products.models import Product
from django.contrib.auth.decorators import login_required
from orders.models import Order, OrderItem
from products.models import Product
from django.http import HttpResponse


def cart_add(request, id):

    cart = request.session.get('cart', {})

    id = str(id)

    if id in cart:
        cart[id] += 1
    else:
        cart[id] = 1

    request.session['cart'] = cart

    return redirect('/cart/')


def cart_increase(request, product_id):

    cart = request.session.get('cart', {})

    product_id = str(product_id)

    if product_id in cart:

        cart[product_id] += 1

    request.session['cart'] = cart

    return redirect('/cart/')


def cart_decrease(request, product_id):

    cart = request.session.get('cart', {})

    product_id = str(product_id)

    if product_id in cart:

        cart[product_id] -= 1

        if cart[product_id] <= 0:

            del cart[product_id]

    request.session['cart'] = cart

    return redirect('/cart/')



def cart_detail(request):

    cart = request.session.get('cart', {})

    products = []

    total = 0

    for product_id, quantity in cart.items():

        product = Product.objects.get(
            id=product_id
        )

        product.quantity = quantity

        product.total_price = (
            product.price * quantity
        )

        total += product.total_price

        products.append(product)

    coupon_data = request.session.get(
        'coupon'
    )

    discount_amount = 0

    final_total = total

    if coupon_data:

        discount_percent = coupon_data[
            'discount'
        ]

        discount_amount = (
            total * discount_percent
        ) / 100

        final_total = total - discount_amount

    return render(
        request,
        'cart/detail.html',
        {
            'products': products,
            'total': total,
            'final_total': final_total,
            'discount_amount': discount_amount,
            'coupon_data': coupon_data
        }
    )


@login_required
def checkout(request):

    cart = request.session.get('cart', {})

    if not cart:

        return HttpResponse(
            'Cart is empty'
        )

    total = 0

    for product_id, quantity in cart.items():

        product = Product.objects.get(
            id=product_id
        )

        if product.stock < quantity:

            return HttpResponse(
                f'{product.name} is out of stock'
            )

        total += product.price * quantity

    coupon_data = request.session.get(
        'coupon'
    )

    discount_amount = 0

    if coupon_data:

        discount_percent = coupon_data[
            'discount'
        ]

        discount_amount = (
            total * discount_percent
        ) / 100

        total -= discount_amount

    order = Order.objects.create(
        user=request.user,
        total_price=total,
        payment_status=True
    )

    for product_id, quantity in cart.items():

        product = Product.objects.get(
            id=product_id
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price
        )

        product.stock -= quantity

        product.save()

    request.session['cart'] = {}

    if 'coupon' in request.session:

        del request.session['coupon']

    return redirect(
        f'/orders/payment/{order.id}/'
    )

def cart_remove(request, id):

    cart = request.session.get('cart', {})

    id = str(id)

    if id in cart:
        del cart[id]

    request.session['cart'] = cart

    return redirect('/cart/')