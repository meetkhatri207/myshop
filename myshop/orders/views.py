import razorpay
from io import BytesIO
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

# ReportLab Imports for PDF Generation
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect

# Models
from .models import Order, OrderItem, Coupon, ShippingAddress
from products.models import Product  # Assumed structured location based on your dependencies

# Initialize Razorpay Client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@login_required
def create_order(request):
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('/cart/')
    
    coupon_data = request.session.get('coupon')
    
    # Calculate totals
    subtotal = Decimal('0')
    products_dict = {}
    
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            products_dict[product_id] = product
            subtotal += Decimal(str(product.price)) * Decimal(str(quantity))
        except Product.DoesNotExist:
            continue
    
    # Calculate discount
    discount_amount = Decimal('0')
    final_total = subtotal
    coupon_code = None
    
    if coupon_data:
        try:
            coupon = Coupon.objects.get(code=coupon_data['code'], active=True)
            if subtotal >= Decimal(str(coupon.minimum_order_amount)):
                if coupon.discount_type == 'percentage':
                    discount_amount = (subtotal * Decimal(str(coupon.amount))) / 100
                elif coupon.discount_type == 'flat':
                    discount_amount = Decimal(str(coupon.amount))
                
                final_total = subtotal - discount_amount
                coupon_code = coupon.code
        except Coupon.DoesNotExist:
            pass
    
    # Get shipping address
    shipping_address_id = request.session.get('shipping_address_id')
    if not shipping_address_id:
        messages.error(request, "Please provide shipping address first.")
        return redirect('/orders/shipping-address/')
    
    try:
        shipping_address = ShippingAddress.objects.get(id=shipping_address_id, user=request.user)
    except ShippingAddress.DoesNotExist:
        messages.error(request, "Shipping address not found.")
        return redirect('/orders/shipping-address/')
    
    # Create order with all amounts
    order = Order.objects.create(
        user=request.user,
        shipping_address=shipping_address,
        subtotal=subtotal,
        discount_amount=discount_amount,
        final_total=final_total,
        coupon_code=coupon_code,
        total_price=final_total,  # Keep for backwards compatibility
        payment_status=False
    )
    
    # Create order items
    for product_id, quantity in cart.items():
        if product_id in products_dict:
            product = products_dict[product_id]
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=int(quantity),
                price=product.price
            )
    
    # Clear cart
    request.session['cart'] = {}
    
    # Redirect directly to backend payment processing initializer
    return redirect('payment_page', order_id=order.id)


@login_required
def payment_page(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user, payment_status=False)
    except Order.DoesNotExist:
        messages.error(request, "Order not found or already processed.")
        return redirect('/cart/')

    subtotal = float(order.subtotal) if order.subtotal else 0
    discount_amount = float(order.discount_amount) if order.discount_amount else 0
    final_total = float(order.final_total) if order.final_total else float(order.total_price)
    
    if final_total <= 0:
        messages.error(request, "Invalid order amount.")
        return redirect('/cart/')

    # Convert to paise
    amount_in_paise = int(final_total * 100)
    
    if amount_in_paise > 50000000:
        messages.error(request, "Amount exceeds gateway limits.")
        return redirect('/cart/')

    try:
        payment = razorpay_client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "payment_capture": 1
        })
    except Exception as e:
        messages.error(request, f"Gateway Error: {str(e)}")
        return redirect('/cart/')

    # Save Razorpay order ID to model instance
    order.razorpay_order_id = payment['id']
    order.save()

    return render(request, 'orders/payment.html', {
        'order': order,
        'payment': payment,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'discount_amount': discount_amount,
        'final_total': final_total,
        'subtotal': subtotal
    })


@csrf_exempt # Razorpay sends an external POST request; skip standard CSRF tokens
def payment_callback(request):
    if request.method == "POST":
        try:
            # Extract tracking tokens passed back from Razorpay
            payment_id = request.POST.get('razorpay_payment_id', '')
            provider_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')

            # Initialize client connection
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            # Cryptographically verify signature integrity
            params_dict = {
                'razorpay_order_id': provider_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            client.utility.verify_payment_signature(params_dict)

            # Match and pull order based on your model field tracking the provider ID
            order = get_object_or_404(Order, razorpay_order_id=provider_order_id)
            order.status = 'Paid' # Or however your application tracks completion state
            order.payment_id = payment_id
            order.save()

            # Safely send the user to your app's payment success or order invoice screen
            return redirect('orders:invoice', order_id=order.id)

        except razorpay.errors.SignatureVerificationError:
            return HttpResponseBadRequest("Tampered payment payload or signature verification failed.")
        except Exception as e:
            return HttpResponseBadRequest(f"An unexpected error occurred processing callback: {str(e)}")
            
    return HttpResponseBadRequest("Invalid request method.")


def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        
        try:
            coupon = Coupon.objects.get(code=code, active=True)
            cart = request.session.get('cart', {})
            total = 0
            
            for product_id, quantity in cart.items():
                product = Product.objects.get(id=product_id)
                total += (product.price * quantity)
            
            if total < coupon.minimum_order_amount:
                return HttpResponse(f'Minimum order should be ₹{coupon.minimum_order_amount}')
            
            request.session['coupon'] = {
                'code': coupon.code,
                'amount': float(coupon.amount),
                'discount_type': coupon.discount_type,
                'minimum_order_amount': float(coupon.minimum_order_amount)
            }
            
        except Coupon.DoesNotExist:
            return HttpResponse('Invalid Coupon')
    
    return redirect('/cart/')


def remove_coupon(request):
    if 'coupon' in request.session:
        del request.session['coupon']
    return redirect('/cart/')


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-id')
    return render(request, 'orders/my_orders.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    return render(request, 'orders/detail.html', {'order': order, 'order_items': order_items})


@login_required
def shipping_address(request):
    if request.method == 'POST':
        address = ShippingAddress.objects.create(
            user=request.user,
            full_name=request.POST.get('full_name'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            pincode=request.POST.get('pincode')
        )
        request.session['shipping_address_id'] = address.id
        return redirect('create_order')
    
    return render(request, 'orders/shipping_address.html')


@login_required
def invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2E7D32'),
        alignment=TA_CENTER,
        spaceAfter=30,
        fontName='Helvetica-Bold'
    )
    
    header_data = [
        [Paragraph("<b><font color='#2E7D32'>MyShop</font></b>", title_style), 
         Paragraph("<b>INVOICE</b><br/><font size=10>Tax Invoice/Bill of Supply</font>", 
                   ParagraphStyle('Invoice', parent=styles['Normal'], alignment=TA_RIGHT))]
    ]
    
    header_table = Table(header_data, colWidths=[250, 200])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    line = Drawing(450, 2)
    line.add(Rect(0, 0, 450, 2, fill=True, stroke=False, fillColor=colors.HexColor('#4CAF50')))
    elements.append(line)
    elements.append(Spacer(1, 20))
    
    created_date = order.created_at if order.created_at else timezone.now()
    info_data = [
        ['INVOICE DETAILS', ''],
        ['Invoice No:', f'INV-{order.id:06d}'],
        ['Invoice Date:', created_date.strftime('%d %B, %Y')],
        ['Order ID:', f'ORD-{order.id:06d}'],
        ['Payment Status:', '<b>Paid</b>' if order.payment_status else 'Pending'],
    ]
    
    info_table = Table(info_data, colWidths=[120, 280])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#1565C0')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 12),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('BACKGROUND', (0, 1), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#37474F')),
        ('TEXTCOLOR', (1, 1), (1, -1), colors.HexColor('#616161')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 1), (1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('BOX', (0, 0), (1, -1), 1, colors.HexColor('#1565C0')),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    shipping_addr = order.shipping_address
    customer_data = [
        ['CUSTOMER INFORMATION', 'SHIPPING ADDRESS'],
        ['Customer Name:', order.user.get_full_name() or order.user.username, 
         'Full Name:', shipping_addr.full_name if shipping_addr else 'N/A'],
        ['Email:', order.user.email, 
         'Phone:', shipping_addr.phone if shipping_addr else 'N/A'],
        ['Member Since:', request.user.date_joined.strftime('%B %Y') if hasattr(request.user, 'date_joined') else 'N/A', 
         'Address:', shipping_addr.address if shipping_addr else 'N/A'],
        ['', '', 'City/State:', f"{shipping_addr.city}, {shipping_addr.state}" if shipping_addr else 'N/A'],
        ['', '', 'Pincode:', shipping_addr.pincode if shipping_addr else 'N/A'],
    ]
    
    customer_table = Table(customer_data, colWidths=[110, 140, 110, 140])
    customer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (3, 0), colors.HexColor('#FF9800')),
        ('TEXTCOLOR', (0, 0), (3, 0), colors.white),
        ('FONTNAME', (0, 0), (3, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (3, 0), 12),
        ('ALIGN', (0, 0), (3, 0), 'CENTER'),
        ('SPAN', (0, 0), (1, 0)),
        ('SPAN', (2, 0), (3, 0)),
        ('BACKGROUND', (0, 1), (3, -1), colors.white),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 1), (3, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('BOX', (0, 0), (3, -1), 1, colors.HexColor('#FF9800')),
    ]))
    
    elements.append(customer_table)
    elements.append(Spacer(1, 25))
    
    products_data = [
        ['S.No', 'PRODUCT NAME', 'QUANTITY', 'UNIT PRICE (₹)', 'TOTAL (₹)']
    ]
    
    serial_no = 1
    for item in order_items:
        qty = Decimal(str(item.quantity))
        price = Decimal(str(item.price))
        item_total = qty * price
        
        products_data.append([
            str(serial_no),
            Paragraph(str(item.product.name), styles['Normal']),
            str(item.quantity),
            f'₹ {float(price):.2f}',
            f'₹ {float(item_total):.2f}'
        ])
        serial_no += 1
    
    while len(products_data) < 6:
        products_data.append(['', '', '', '', ''])
    
    product_table = Table(products_data, colWidths=[40, 300, 60, 80, 80])
    product_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('ALIGN', (3, 1), (4, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDBDBD')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2E7D32')),
    ]))
    
    elements.append(product_table)
    elements.append(Spacer(1, 20))
    
    # Dynamic Order Totals System mapped perfectly to your Database fields
    subtotal_val = float(order.subtotal)
    discount_val = float(order.discount_amount)
    final_total_val = float(order.final_total)
    
    summary_data = [
        ['SUMMARY', ''],
        ['Subtotal:', f'₹ {subtotal_val:.2f}'],
        ['Discount Applied:', f'- ₹ {discount_val:.2f}'],
        ['Shipping Charges:', '₹ 0.00'],
        ['Total Paid Amount:', f'₹ {final_total_val:.2f}'],
    ]
    
    summary_table = Table(summary_data, colWidths=[350, 100])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#1565C0')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('BACKGROUND', (0, 1), (1, -2), colors.white),
        ('FONTNAME', (0, 1), (0, -2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -2), 10),
        ('BACKGROUND', (0, -1), (1, -1), colors.HexColor('#FFC107')),
        ('TEXTCOLOR', (0, -1), (1, -1), colors.black),
        ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 1), (1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('BOX', (0, 0), (1, -1), 1, colors.HexColor('#1565C0')),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    thank_you_style = ParagraphStyle(
        'ThankYou', parent=styles['Normal'], fontSize=11, 
        textColor=colors.HexColor('#2E7D32'), alignment=TA_CENTER, fontName='Helvetica-Bold'
    )
    elements.append(Paragraph("<b>Thank you for shopping with us!</b>", thank_you_style))
    
    footer_style = ParagraphStyle(
        'Footer', parent=styles['Normal'], fontSize=8, 
        textColor=colors.HexColor('#9E9E9E'), alignment=TA_CENTER
    )
    elements.append(Paragraph("<br/><hr/><br/>This is a system generated invoice and does not require a physical signature.<br/>For any queries, please contact support@myshop.com", footer_style))
    
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'
    response.write(pdf)
    
    return response