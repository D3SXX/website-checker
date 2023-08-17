import datetime
import json
from bs4 import BeautifulSoup

def process_website_content(website,content,items_amount_old, website_content_listbox):
    print("Identifying the website")
    if "hinta.fi" in website:
        print("Hinta.fi identified")
        entry, entry_xl, items_amount_old = hinta_process_website_content(website,content,items_amount_old, website_content_listbox)

    return entry, entry_xl, items_amount_old
def hinta_process_website_content(website,content,items_amount_old, website_content_listbox):
    items_amount = 0
    entry_xl = []
    soup = BeautifulSoup(content, 'html.parser')
    script_tags = soup.find_all('script', type='application/ld+json')

    if "hinta.fi/g" in website:
        print("scanning category list")
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
                        entry_xl.append((product_name, offer_name, price, currency, seller_name))  # Append data to the list
                        items_amount += 1

            except json.JSONDecodeError:
                pass  # Skip this script if it's not valid JSON

        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"{current_time} - The site's listings were updated (from {items_amount_old} to {items_amount})..."
        items_amount_old = items_amount

        return entry, entry_xl, items_amount_old
    else:
        print("Scanning product list")

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

    return entry, entry_xl, items_amount_old
