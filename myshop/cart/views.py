from django.shortcuts import render, redirect, get_object_or_404
from products.models import Product
from django.contrib.auth.decorators import login_required
from orders.models import Order, OrderItem, ShippingAddress, Coupon
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

    return redirect('/products/')


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

    cart = request.session.get(
        'cart',
        {}
    )

    products = []

    total = 0

    # ACTIVE COUPONS

    coupons = Coupon.objects.filter(
        active=True
    )

    # CART PRODUCTS

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

    # DEFAULT VALUES

    discount_amount = 0

    final_total = total

    # SESSION COUPON

    coupon_data = request.session.get( 'coupon', {} )
    amount = coupon_data.get( 'amount', 0 )

    # APPLY COUPON

    if coupon_data:

        try:

            coupon = Coupon.objects.get(
                code=coupon_data['code'],
                active=True
            )

            # MINIMUM ORDER VALIDATION

            if total < coupon.minimum_order_amount:

                del request.session['coupon']

                coupon_data = None

            else:

                # PERCENTAGE DISCOUNT

                if coupon.discount_type == 'percentage':

                    discount_amount = (
                        total * coupon.amount
                    ) / 100

                # FLAT DISCOUNT

                elif coupon.discount_type == 'flat':

                    discount_amount = coupon.amount

                # FINAL TOTAL

                final_total = round(
                    total - discount_amount, 2
                )

                # PREVENT NEGATIVE TOTAL

                if final_total < 0:

                    final_total = 0

        except Coupon.DoesNotExist:

            if 'coupon' in request.session:

                del request.session['coupon']

            coupon_data = None

    return render(

        request,

        'cart/detail.html',

        {

            'products': products,

            'total': total,

            'discount_amount': discount_amount,

            'final_total': final_total,

            'coupon_data': coupon_data,

            'coupons': coupons

        }
    )


@login_required
def checkout(request):

    cart = request.session.get('cart', {})

    address_id = request.session.get(
        'shipping_address_id'
    )

    shipping_address = ShippingAddress.objects.get(
        id=address_id
    )

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
        'coupon',
        {}
    )

    discount_amount = 0

    if coupon_data:

        amount = coupon_data.get(
            'amount',
            0
        )

        discount_type = coupon_data.get(
            'discount_type',
            ''
        )

        if discount_type == 'percentage':

            discount_amount = (
                total * amount
            ) / 100

        elif discount_type == 'flat':

            discount_amount = amount


    order = Order.objects.create(
        user=request.user,
        total_price=total,
        payment_status=True,
        shipping_address=shipping_address
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