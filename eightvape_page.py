import requests
from bs4 import BeautifulSoup
import re
import time
import csv
from datetime import datetime
import logging
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

# CSV file configuration
CSV_FILE = 'eightvape_products.csv'
CSV_FIELDS = ['product_id', 'product_name', 'category', 'flavor', 'nicotine_level', 'brand']

# ========== UTILS ==========
def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    return ' '.join(text.strip().split())

def extract_flavor(product_name):
    """Improved flavor extraction with multiple patterns"""
    patterns = [
        r' - ([^-]+)$',  # After last dash
        r'\((.*?)\)',    # In parentheses
        r'\[(.*?)\]'      # In brackets
    ]
    
    for pattern in patterns:
        match = re.search(pattern, product_name)
        if match:
            return clean_text(match.group(1))
    return "Unknown"

def extract_nicotine(product_name):
    """More precise nicotine extraction"""
    patterns = [
        r'(\d+\s?mg)',       # 3mg, 6mg etc
        r'(\d+\.?\d*\s?%)',   # 1.5%, 3% etc
        r'(\d+\s?ml)'         # 30ml, 60ml etc
    ]
    
    for pattern in patterns:
        match = re.search(pattern, product_name, re.IGNORECASE)
        if match:
            return match.group(0).lower()
    return "Unknown"

def init_csv_file():
    """Initialize CSV file with headers"""
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()

def save_to_csv(product):
    """Save product data to CSV file"""
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writerow({
            'product_id': '',  # Will be auto-incremented in database
            'product_name': product['product_name'],
            'category': product['category'],
            'flavor': product['flavor'],
            'nicotine_level': product['nicotine_level'],
            'brand': product['brand']
        })

# ========== SCRAPER ==========
def scrape_eightvape_page(page_number=1):
    """Scrape a single page of EightVape products"""
    base_url = "https://www.eightvape.com"
    url = f"{base_url}/collections/vape-juice?page={page_number}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch page {page_number}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'lxml')
    product_cards = soup.select('div.grid-product__content')

    products = []
    
    for card in product_cards:
        try:
            title_el = card.select_one('.grid-product__title')
            price_el = card.select_one('.grid-product__price span')
            link_el = card.select_one('a.grid-product__link')

            if not title_el:
                continue

            name = clean_text(title_el.get_text())
            price = clean_text(price_el.get_text()) if price_el else '0'

            product = {
                'product_name': name,
                'brand': 'Unknown',  # You might scrape this from product detail page
                'category': 'Vape Juice',
                'flavor': extract_flavor(name),
                'nicotine_level': extract_nicotine(name)
            }
            products.append(product)
        except Exception as e:
            logging.error(f"Error processing product card: {e}")
            continue

    return products

# ========== MAIN ==========
def main():
    # Initialize CSV file
    init_csv_file()
    all_products = []
    max_pages = 3  # Adjust as needed
    retries = 3
    
    # Scrape multiple pages
    for page in range(1, max_pages + 1):
        for attempt in range(retries):
            try:
                logging.info(f"Scraping page {page} (attempt {attempt + 1})")
                products = scrape_eightvape_page(page)
                all_products.extend(products)
                
                # Save products to CSV
                for product in products:
                    save_to_csv(product)
                
                time.sleep(2 + attempt)  # Increasing delay for retries
                break
            except Exception as e:
                logging.error(f"Error on page {page}: {e}")
                if attempt == retries - 1:
                    logging.error(f"Failed after {retries} attempts for page {page}")
                time.sleep(5 * (attempt + 1))

    logging.info(f"Scraped {len(all_products)} products total")
    logging.info(f"Data saved to {CSV_FILE}")

if __name__ == "__main__":
    start_time = time.time()
    main()
    logging.info(f"Execution time: {time.time() - start_time:.2f} seconds")
