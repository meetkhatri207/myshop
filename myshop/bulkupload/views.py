import pandas as pd

from django.shortcuts import render

from products.models import Product, Category

from .models import ImportHistory


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

                    # CREATE / UPDATE PRODUCT

                    Product.objects.update_or_create(

                        name=name,

                        defaults={

                            'price': price,

                            'stock': stock,

                            'category': category,

                            'description': description

                        }

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