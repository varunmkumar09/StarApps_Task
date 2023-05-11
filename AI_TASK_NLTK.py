import time
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import json
import spacy
import re
import numpy as np

nlp = spacy.load('en_core_web_sm')
color_names = ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'pink', 'brown', 'gray', 'black', 'white','navy']
color_pattern = re.compile(r'color:?\s+(\w+)', re.IGNORECASE)

def extract_colors(text):
    """
    Extracts color-related words from a text string using spaCy and regular expressions.
    """
    doc = nlp(text)
    colors = set()
    for token in doc:
        if token.text.lower() in color_names:
            colors.add(token.text.lower())

    matches = re.findall(color_pattern, text)
    for match in matches:
        if match.lower() in color_names:
            colors.add(match.lower())

    return list(colors)


def FindAllGroups(store_domain):
    products = []
    page_number = 1
    while True:
        url = f"https://{store_domain}/collections/all/products.json?page={page_number}"
        try:
            response = requests.get(url)
            page_data = response.json()
        except:
            break

        if not isinstance(page_data["products"], list):
            print("No products found on this page.")
            break
        products.extend(page_data["products"])
        page_number += 1
        if page_number == 50:
            break
        time.sleep(1)

    product_data = []
    for product in products:
        title = product['title']
        product_type = product['product_type']
        variants = [(v['title'], v['price'], v['option1']) for v in product['variants']]
        product_data.append(f"{title} {product_type} {' '.join([f'{v[0]} {v[1]}' for v in variants])}")

    color_tags = []
    for product in products:
        title = product['title']
        color_text = product['tags']
        for text in color_text:
            colors = extract_colors(text)
            if colors:
                color_tags.append({'product': title, 'color': colors})
                break
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        X = vectorizer.fit_transform(product_data)
        num_clusters = 20
        km = KMeans(n_clusters=num_clusters)
        km.fit(X)
    except:
        return "No products found"

    # Elbow method. For dynamic K value
    # try:
    #     vectorizer = TfidfVectorizer(stop_words='english')
    #     X = vectorizer.fit_transform(product_data)
    #     sse = []
    #     for k in range(1, len(products)):
    #         km = KMeans(n_clusters=k)
    #         km.fit(X)
    #         sse.append(km.inertia_)
    #     optimal_k = np.argmin(np.diff(sse)) + 1
    #     km = KMeans(n_clusters=optimal_k)
    #     km.fit(X)
    # except:
    #     return "No products found"

    groups = {}
    for i, label in enumerate(km.labels_):
        if label not in groups:
            groups[label] = []
        product_link = products[i]['handle']
        product_url = f"https://{store_domain}/products/{product_link}"

        product_title = products[i]['title']
        for color_tag in color_tags:
            if color_tag['product'] == product_title:
                product_url += f"?color={color_tag['color']}"
                break
        groups[label].append(product_url)

    result = [{'product variations': v} for v in groups.values()]
    return json.dumps(result, indent=4)

store_domain = 'boysnextdoor-apparel.co'
result = FindAllGroups(store_domain)
print(result)