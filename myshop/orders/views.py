import razorpay
from django.shortcuts import get_object_or_404, render
from .models import Order, OrderItem, Coupon
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, Line
from reportlab.graphics import renderPDF
from io import BytesIO
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from decimal import Decimal


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

    print(order)

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
            'order_items': order_items
        }
    )


from .models import ShippingAddress


@login_required
def shipping_address(request):

    if request.method == 'POST':

        address = ShippingAddress.objects.create(

            user=request.user,

            full_name=request.POST.get(
                'full_name'
            ),

            phone=request.POST.get(
                'phone'
            ),

            address=request.POST.get(
                'address'
            ),

            city=request.POST.get(
                'city'
            ),

            state=request.POST.get(
                'state'
            ),

            pincode=request.POST.get(
                'pincode'
            )
        )

        request.session[
            'shipping_address_id'
        ] = address.id

        return redirect(
            '/cart/checkout/'
        )

    return render(
        request,
        'orders/shipping_address.html'
    )

@login_required
def invoice_pdf(request, order_id):

    order = Order.objects.get(
        id=order_id,
        user=request.user
    )

    order_items = OrderItem.objects.filter(
        order=order
    )

    # Create buffer for PDF
    buffer = BytesIO()
    
    # Create document with custom page size
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )
    
    # Container for story elements
    elements = []
    
    # Custom styles
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
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.white,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1565C0'),
        spaceAfter=20,
        fontName='Helvetica-Bold'
    )
    
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#424242'),
        spaceAfter=6,
        fontName='Helvetica'
    )
    
    # Header with logo/title
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
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 28),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#2E7D32')),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Divider line
    line = Drawing(450, 2)
    line.add(Rect(0, 0, 450, 2, fill=True, stroke=False, fillColor=colors.HexColor('#4CAF50')))
    elements.append(line)
    elements.append(Spacer(1, 20))
    
    # Order Information Box
    info_data = [
        ['INVOICE DETAILS', ''],
        ['Invoice No:', f'INV-{order.id:06d}'],
        ['Invoice Date:', order.created_at.strftime('%d %B, %Y') if hasattr(order, 'created_at') else 'N/A'],
        ['Order ID:', f'ORD-{order.id:06d}'],
        ['Order Date:', order.created_at.strftime('%d %B, %Y %I:%M %p') if hasattr(order, 'created_at') else 'N/A'],
        ['Payment Status:', '<b>Paid</b>'],
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
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 1), (1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('BOX', (0, 0), (1, -1), 1, colors.HexColor('#1565C0')),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    # Customer Information Box
    customer_data = [
        ['CUSTOMER INFORMATION', 'SHIPPING ADDRESS'],
        ['Customer Name:', order.user.get_full_name() or order.user.username, 'Full Name:', order.shipping_address.full_name if order.shipping_address else 'N/A'],
        ['Email:', order.user.email, 'Phone:', order.shipping_address.phone if order.shipping_address else 'N/A'],
        ['Member Since:', request.user.date_joined.strftime('%B %Y') if hasattr(request.user, 'date_joined') else 'N/A', 'Address:', order.shipping_address.address if order.shipping_address else 'N/A'],
        ['', '', 'City/State:', f"{order.shipping_address.city}, {order.shipping_address.state}" if order.shipping_address else 'N/A'],
        ['', '', 'Pincode:', order.shipping_address.pincode if order.shipping_address else 'N/A'],
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
        ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#37474F')),
        ('TEXTCOLOR', (1, 1), (1, -1), colors.HexColor('#616161')),
        ('TEXTCOLOR', (2, 1), (2, -1), colors.HexColor('#37474F')),
        ('TEXTCOLOR', (3, 1), (3, -1), colors.HexColor('#616161')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
        ('FONTNAME', (3, 1), (3, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 1), (3, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('BOX', (0, 0), (3, -1), 1, colors.HexColor('#FF9800')),
    ]))
    
    elements.append(customer_table)
    elements.append(Spacer(1, 25))
    
    # Product Items Table
    products_data = [
        ['S.No', 'PRODUCT NAME', 'QUANTITY', 'UNIT PRICE (₹)', 'TOTAL (₹)']
    ]
    
    serial_no = 1
    subtotal = 0
    
    for item in order_items:
        item_total = Decimal(str(item.quantity)) * item.price
        subtotal += item_total
        
        products_data.append([
            str(serial_no),
            Paragraph(item.product.name, styles['Normal']),
            str(item.quantity),
            f'₹ {item.price:.2f}',
            f'₹ {item_total:.2f}'
        ])
        serial_no += 1
    
    # Add empty rows if needed for consistent height
    while len(products_data) < 10:
        products_data.append(['', '', '', '', ''])
    
    product_table = Table(products_data, colWidths=[40, 250, 60, 80, 80])
    product_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#424242')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('ALIGN', (3, 1), (4, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDBDBD')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2E7D32')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
    ]))
    
    elements.append(product_table)
    elements.append(Spacer(1, 20))
    
    # Summary Box
    tax_rate = Decimal('0.18')  # 18% GST
    tax_amount = subtotal * tax_rate
    total = subtotal + tax_amount
    
    summary_data = [
        ['SUMMARY', ''],
        ['Subtotal:', f'₹ {subtotal:.2f}'],
        [f'GST ({int(tax_rate * 100)}%):', f'₹ {tax_amount:.2f}'],
        ['Shipping Charges:', '₹ 0.00'],
        ['Total Amount:', f'₹ {total:.2f}'],
    ]
    
    summary_table = Table(summary_data, colWidths=[350, 100])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#1565C0')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 12),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('BACKGROUND', (0, 1), (1, -2), colors.white),
        ('TEXTCOLOR', (0, 1), (0, -2), colors.HexColor('#37474F')),
        ('TEXTCOLOR', (1, 1), (1, -2), colors.HexColor('#616161')),
        ('FONTNAME', (0, 1), (0, -2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -2), 10),
        ('BACKGROUND', (0, -1), (1, -1), colors.HexColor('#FFC107')),
        ('TEXTCOLOR', (0, -1), (1, -1), colors.HexColor('#000000')),
        ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 1), (1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('BOX', (0, 0), (1, -1), 1, colors.HexColor('#1565C0')),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Thank You Message
    thank_you_style = ParagraphStyle(
        'ThankYou',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2E7D32'),
        alignment=TA_CENTER,
        spaceAfter=20,
        fontName='Helvetica-Bold'
    )
    
    elements.append(Paragraph("<b>Thank you for shopping with us!</b>", thank_you_style))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#9E9E9E'),
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph("<br/><hr/><br/>This is a system generated invoice and does not require signature.<br/>For any queries, please contact support@myshop.com", footer_style))
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF from buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'
    response.write(pdf)
    
    return response