from django.shortcuts import render,get_object_or_404
from .models import Product, Category
from reviews.models import Review
from django.db.models import Avg


def product_list(request):
    search = request.GET.get('search')

    category_id = request.GET.get('category')

    products = Product.objects.all()

    categories = Category.objects.all()

    selected_category = request.GET.get('category') 

    

    if search:
        products = products.filter(
            name__icontains=search
        )

    if category_id:

        products = products.filter(
            category_id=category_id
        )

    return render(request, 'products/index.html', {
        'products': products,
        'categories': categories,
        'selected_category': selected_category
    })

def product_detail(request, id):

    product = get_object_or_404(Product, id=id)

    reviews = Review.objects.filter(
        product=product
    )

    avg_rating = Review.objects.filter(
        product=product
    ).aggregate(avg=Avg('rating'))

    return render(request, 'products/detail.html', {
        'product': product,
        'reviews' : reviews,
        'avg_rating': avg_rating['avg']
    })