import datetime
import json
from bs4 import BeautifulSoup
import re

def process_website_content(website,content,items_amount_old, website_content_listbox):
    print("Identifying the website")
    if "hinta.fi" in website:
        print("Hinta.fi identified")
        entry, entry_xl, items_amount_old, columns = hinta_process_website_content(website,content,items_amount_old, website_content_listbox)

    return entry, entry_xl, items_amount_old, columns
def hinta_process_website_content(website,content,items_amount_old, website_content_listbox):
    items_amount = 0
    entry_xl = []
    soup = BeautifulSoup(content, 'html.parser')
    script_tags = soup.find_all('script', type='application/ld+json')

    if "hinta.fi/g" in website:
        print("Scanning category list (/g)")
        
        product_rows = soup.find_all('tr', class_='hvjs-product-row')

        for row in product_rows:
            product_name_tag = row.find('strong', class_='hv--name')
            product_name = product_name_tag.get_text() if product_name_tag else "Unknown Product"
            link_tag = row.find('a', href=True)
            category_link = link_tag['href'] if link_tag else "Unknown Link"
            price_tag = row.find('td', class_='hv--price')
            price = price_tag.a.get_text() if price_tag else "Unknown Price"
            if not price[-1].isdigit():
                currency = price[-1]
                price = price[:-2]
                price = price.replace(',', '.')
                price = price.replace(' ', '')
            else:
                currency = "Unknown Currency"
            entry_xl.append((product_name, price,currency,"https://hinta.fi" + category_link))
            items_amount += 1

        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"{current_time} - The site's listings were updated (from {items_amount_old} to {items_amount})..."
        items_amount_old = items_amount
        columns = ("Item","Price","Currency","Link")
        return entry, entry_xl, items_amount_old, columns
    elif re.match(r'https://hinta\.fi/\d+/.*', website):
        print("Scanning product list (\d+/.*)")
        for script in script_tags:
            try:
                product_data = json.loads(script.string)
                if "@type" in product_data and product_data["@type"] == "Product":
                    product_name = product_data["name"] if "name" in product_data else "Unknown Product"
                    offers = product_data.get("offers", {}).get("offers", [])

                    for offer in offers:
                        offer_name = offer.get("name", "Unknown Offer")
                        price = offer.get("price", "Unknown Price")
                        currency = offer.get("priceCurrency", "EUR")
                        seller_name = offer.get("seller", {}).get("name", "Unknown Seller")

                        entry = f"Item: {product_name} Offer: {offer_name} Price: {price} {currency} Seller: {seller_name}"
                        entry_xl.append((offer_name, seller_name , price, currency))
                        items_amount += 1

            except json.JSONDecodeError:
                pass  # Skip this script if it's not valid JSON

        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"{current_time} - The site's listings were updated (from {items_amount_old} to {items_amount})..."
        items_amount_old = items_amount
        columns = ("Item","Seller","Price","Currency")
        return entry, entry_xl, items_amount_old, columns
    elif "hinta.fi" in website:
        print("Scanning main page")
        category_links = soup.find_all('a', class_='hv-menu-i-a')
        entry_xl = []

        for link in category_links:
            category_name = link.text
            category_link = link['href']
            
            # Check if the link contains unwanted patterns, skip if it does
            if "hv-store-logo-w" in link.parent.attrs.get("class", []) or "kauppaan.php" in category_link:
                continue
            
            # Replace spaces with an underscore
            category_name_fixed = "_".join(category_name.split())
            
            entry_xl.append((category_name_fixed, "https://hinta.fi" + category_link))
            items_amount += 1

        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"{current_time} - The site's listings were updated (from {items_amount_old} to {items_amount})..."
        
        items_amount_old = items_amount
        items_amount = len(entry_xl)

        columns = ("Category", "Link")
        
        return entry, entry_xl, items_amount_old, columns
