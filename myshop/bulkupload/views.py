import pandas as pd

import os

import requests

from django.core.files.base import ContentFile

from django.core.files import File

from django.shortcuts import render

from products.models import Product, Category

from .models import ImportHistory

from .ocr_service import extract_text_from_image

from .ai_parser import extract_product_data

import re

from django.http import HttpResponse

from PIL import Image

import pytesseract


def test_ocr(request):

    image = Image.open(
        'media/test_product.png'
    )

    # OCR

    text = pytesseract.image_to_string(image)

    ai_result = extract_product_with_ai(text) 
    
    print(ai_result) 
    
    return HttpResponse(ai_result)

    print(text)

    # AI PARSER

    product_data = extract_product_data(text)

    # SHOW RESULT

    final_output = f"""

    PRODUCT NAME: {product_data['name']}

    PRICE: {product_data['price']}

    STOCK: {product_data['stock']}

    CATEGORY: {product_data['category_name']}

    DESCRIPTION:

    {product_data['description']}

    """

    return HttpResponse(final_output)



def bulk_upload(request):

    errors = []

    success_count = 0

    failed_count = 0

    if request.method == 'POST':

        excel_file = request.FILES.get('file')

        # FILE VALIDATION

        if not excel_file:

            errors.append(
                'Please upload excel file'
            )

            return render(
                request,
                'bulkupload/upload.html',
                {
                    'errors': errors
                }
            )

        # CREATE IMPORT HISTORY

        history = ImportHistory.objects.create(

            uploaded_by=request.user,

            file_name=excel_file.name,

            status='processing'

        )

        try:

            # READ EXCEL

            df = pd.read_excel(excel_file)

            # TOTAL ROWS

            history.total_rows = len(df)

            history.save()

            # LOOP ROWS

            for index, row in df.iterrows():

                try:

                    # GET VALUES

                    name = str(
                        row['name']
                    ).strip()

                    price = float(
                        row['price']
                    )

                    stock = int(
                        row['stock']
                    )

                    category_name = str(
                        row['category']
                    ).strip()

                    description = str(
                        row['description']
                    ).strip()

                    image_name = str( 
                        row['image'] 
                    ).strip()

                    # VALIDATIONS

                    if not name:

                        errors.append(
                            f'Row {index + 1} -> Name missing'
                        )

                        failed_count += 1

                        continue

                    if price < 0:

                        errors.append(
                            f'{name} -> Invalid price'
                        )

                        failed_count += 1

                        continue

                    if stock < 0:

                        errors.append(
                            f'{name} -> Invalid stock'
                        )

                        failed_count += 1

                        continue

                    # CATEGORY

                    category, created = (
                        Category.objects.get_or_create(
                            name=category_name
                        )
                    )


                    product, created = Product.objects.update_or_create(

                        name=name,

                        defaults={

                            'price': price,

                            'stock': stock,

                            'category': category,

                            'description': description

                        }

                    )

                    # IMAGE PATH

                    image_path = os.path.join(

                        'media/product_images/',
                        image_name

                    )

                    # IMAGE URL

                    image_path = str(
                        row['image']
                    ).strip()

                    # IMAGE DOWNLOAD

                    if image_path:

                        try:

                            headers = {

                                "User-Agent": "Mozilla/5.0"

                            }

                            response = requests.get(

                                image_path,

                                headers=headers,

                                timeout=10

                            )

                            if response.status_code == 200:

                                image_name = f"{name}.jpg"

                                product.image.save(

                                    image_name,

                                    ContentFile(response.content),

                                    save=True

                                )

                            else:

                                errors.append(

                                    f'{name} -> Image not found'

                                )

                        except Exception as e:

                            errors.append(

                                f'{name} -> Image error: {str(e)}'

                            )



                    success_count += 1

                except Exception as e:

                    failed_count += 1

                    errors.append(

                        f'Row {index + 1} -> {str(e)}'

                    )

            # FINAL HISTORY UPDATE

            history.success_rows = success_count

            history.failed_rows = failed_count

            history.status = 'completed'

            history.save()

        except Exception as e:

            history.status = 'failed'

            history.error_message = str(e)

            history.save()

            errors.append(str(e))

    return render(

        request,

        'bulkupload/upload.html',

        {

            'errors': errors,

            'success_count': success_count,

            'failed_count': failed_count

        }

    )