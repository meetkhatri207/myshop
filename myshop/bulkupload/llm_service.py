from openai import OpenAI

client = OpenAI(
    api_key='YOUR_API_KEY'
)


def extract_product_with_ai(text):

    prompt = f"""

    Extract product information from this text.

    Return ONLY JSON.

    Required fields:

    name
    price
    stock
    category
    description

    TEXT:
    {text}

    """

    response = client.chat.completions.create(

        model="gpt-3.5-turbo",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]

    )

    return response.choices[0].message.content
