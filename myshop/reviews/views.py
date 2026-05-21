from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

from .models import Review
from products.models import Product


@login_required
def add_review(request, product_id):

    if request.method == 'POST':

        product = Product.objects.get(id=product_id)

        rating = request.POST['rating']
        comment = request.POST['comment']

        Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            comment=comment
        )

    return redirect(f'/products/{product_id}/')