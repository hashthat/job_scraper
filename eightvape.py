import requests
from bs4 import BeautifulSoup
import mysql.connector
import re
import time

# ========== DB CONFIG ==========
db_config = {
    'host': 'localhost',
    'user': 'your_mysql_user',
    'password': 'your_mysql_password',
    'database': 'your_database_name'
}

# ========== UTILS ==========
def extract_flavor(product_name):
    # crude example: flavor is whatever comes after the dash
    parts = product_name.split(" - ")
    return parts[1].strip() if len(parts) > 1 else "Unknown"

def extract_nicotine(product_name):
    match = re.search(r'(\d+mg|\d+\s?%|\d+ml)', product_name, re.IGNORECASE)
    return match.group(0) if match else "Unknown"

def insert_product(cursor, product):
    cursor.execute("""
        INSERT INTO dim_product (product_name, brand, category, flavor, nicotine_level)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE product_name = product_name;
    """, (
        product['product_name'],
        product['brand'],
        product['category'],
        product['flavor'],
        product['nicotine_level']
    ))

# ========== SCRAPER ==========
def scrape_eightvape_page(page_number=1):
    url = f"https://www.eightvape.com/collections/vape-juice?page={page_number}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch page {page_number}")
        return []

    soup = BeautifulSoup(response.text, 'lxml')
    product_cards = soup.select('div.grid-product__content')

    products = []

    for card in product_cards:
        title_el = card.select_one('.grid-product__title')
        price_el = card.select_one('.grid-product__price span')

        if not title_el:
            continue

        name = title_el.get_text(strip=True)
        price = price_el.get_text(strip=True) if price_el else '0'

        product = {
            'product_name': name,
            'brand': 'Unknown',  # can be improved via NLP or details scrape
            'category': 'Vape Juice',
            'flavor': extract_flavor(name),
            'nicotine_level': extract_nicotine(name)
        }
        products.append(product)

    return products

# ========== MAIN ==========
def main():
    all_products = []

    # Scrape multiple pages
    for page in range(1, 3):  # you can increase range here
        print(f"Scraping page {page}")
        products = scrape_eightvape_page(page)
        all_products.extend(products)
        time.sleep(2)  # polite pause

    print(f"Scraped {len(all_products)} products")

    # Insert into MySQL
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    for product in all_products:
        insert_product(cursor, product)

    conn.commit()
    cursor.close()
    conn.close()
    print("Data inserted into dim_product.")

if __name__ == "__main__":
    main()
