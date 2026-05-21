from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from orders.models import Order
from wishlist.models import Wishlist
from products.models import Product
from django.contrib.auth.decorators import login_required


def register(request):

    if request.method == 'POST':

        username = request.POST['username']

        email = request.POST['email']

        password = request.POST['password']

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        return redirect('/users/login')

    return render(request, 'users/register.html')


def login_user(request):

    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect('/products/')

        else:

            return render(request, 'users/login.html', {
                'error': 'Invalid username or password'
            })

    return render(request, 'users/login.html')


def logout_user(request):

    logout(request)

    return redirect('/products/')

@login_required
def dashboard(request):

    orders = Order.objects.filter(
        user=request.user
    ).order_by('-id')

    wishlist_items = Wishlist.objects.filter(
        user=request.user
    )

    return render(request, 'users/dashboard.html', {
        'orders': orders,
        'wishlist_items': wishlist_items
    })


    if not request.user.is_staff:

        return redirect('/')

    total_users = User.objects.count()

    total_products = Product.objects.count()

    total_orders = Order.objects.count()

    total_revenue = 0

    orders = Order.objects.filter(
        payment_status=True
    )

    for order in orders:

        total_revenue += order.total_price

    return render(request, 'users/admin_dashboard.html', {

        'total_users': total_users,

        'total_products': total_products,

        'total_orders': total_orders,

        'total_revenue': total_revenue

    })