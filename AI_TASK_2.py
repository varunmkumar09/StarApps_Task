import time

import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import json

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
        time.sleep(1)

    product_data = []
    for product in products:
        title = product['title']
        product_type = product['product_type']
        variants = [(v['title'], v['price']) for v in product['variants']]
        product_data.append(f"{title} {product_type} {' '.join([f'{v[0]} {v[1]}' for v in variants])}")
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        X = vectorizer.fit_transform(product_data)
        num_clusters = 20
        km = KMeans(n_clusters=num_clusters)
        km.fit(X)
    except:
        return "No products found"


    groups = {}
    for i, label in enumerate(km.labels_):
        if label not in groups:
            groups[label] = []
        product_link = products[i]['handle']
        product_url = f"https://{store_domain}/products/{product_link}"
        groups[label].append(product_url)

    result = [{'product variations': v} for v in groups.values()]
    return json.dumps(result, indent=4)


store_domain = 'boysnextdoor-apparel.co'
result = FindAllGroups(store_domain)
print(result)
