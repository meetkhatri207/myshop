import re


def extract_product_data(text):

    data = {

        'name': '',
        'price': 0,
        'stock': 0,
        'category_name': '',
        'description': ''

    }

    # SPLIT LINES

    lines = text.split('\n')

    # REMOVE EMPTY LINES

    lines = [line.strip() for line in lines if line.strip()]

    # NAME

    if lines:

        data['name'] = lines[0]

    # PRICE

    price_match = re.search(

        r'(Price|MRP|Cost)?\s*[:\-]?\s*₹?(\d+)',

        text,

        re.IGNORECASE

    )

    if price_match:

        data['price'] = float(
            price_match.group(2)
        )

    # STOCK

    stock_match = re.search(

        r'(Stock|Qty|Quantity)?\s*[:\-]?\s*(\d+)',

        text,

        re.IGNORECASE

    )

    if stock_match:

        data['stock'] = int(
            stock_match.group(2)
        )

    # CATEGORY DETECTION

    lower_text = text.lower()

    if 'shoe' in lower_text:

        data['category_name'] = 'Footwear'

    elif 'phone' in lower_text:

        data['category_name'] = 'Mobiles'

    elif 'tv' in lower_text:

        data['category_name'] = 'Electronics'

    else:

        data['category_name'] = 'General'

    # DESCRIPTION

    data['description'] = text

    return data