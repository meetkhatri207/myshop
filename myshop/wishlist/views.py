from django.shortcuts import redirect,render,get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Wishlist 
from products.models import Product

def add_to_wishlist(request, product_id):
    product = Product.objects.get(id=product_id)

    already_exists = Wishlist.objects.filter(
        user=request.user,
        product=product
    ).exists()

    if not already_exists:
        Wishlist.objects.create(
            user=request.user,
            product=product
        )

    return redirect('/products/')


def remove_to_wishlist(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id
    )

    Wishlist.objects.filter(
        user=request.user,
        product=product
    ).delete()

    return redirect('/wishlist/')

@login_required
def wishlist_detail(request):

    wishlist_items = Wishlist.objects.filter(
        user=request.user
    )

    return render(request, 'wishlist/detail.html', {
        'wishlist_items': wishlist_items
    })