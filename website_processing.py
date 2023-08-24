import datetime
import json
from bs4 import BeautifulSoup
import re
import requests



def process_website_content(website,content,items_amount_old, website_content_listbox,progress_callback,edit_back_page):
    global back_page_index,back_page
    print("Identifying the website")
        
    if "hinta.fi" in website:
        print("Hinta.fi identified")
        entry, entry_xl, items_amount_old, columns = hinta_process_website_content(website,content,items_amount_old, website_content_listbox,progress_callback)
    
    edit_back_page(website)
    return entry, entry_xl, items_amount_old, columns
def hinta_process_website_content(website,content,items_amount_old, website_content_listbox,progress_callback):

    #global back_page,back_page_index

    items_amount = 0
    entry_xl = []
    soup = BeautifulSoup(content, 'html.parser')
    script_tags = soup.find_all('script', type='application/ld+json')

    if "hinta.fi/g" in website:
        print("Scanning category list (/g)")

        entry_xl.append(("↵ Return to the previous page","","","https://hinta.fi"))

        total_items_element = soup.find('span', class_='hv-text-strong')
        if total_items_element:
            total_items = int(total_items_element.text.replace(',', '.').replace(' ', ''))
        else:
            total_items = 15 # Failback
        print(f"The amount of expected elements is {total_items_element}")

        items_amount = 0
        actual_items_amount = 0
        page_number = 1

        while True:
            try:
                skipped_items = 0
                if items_amount == total_items:
                    print(f"Exiting job ({items_amount} == {total_items})")
                    items_amount = actual_items_amount
                    break
                print(f"Trying to get page {page_number}: {website}?l=1&p={page_number}",end=" ")
                response = requests.get(f"{website}?l=1&p={page_number}", timeout=5)
                print(f"Got response {response.status_code}")
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    product_rows = soup.find_all('tr', class_='hvjs-product-row')

                    for row in product_rows:
                        product_name_tag = row.find('strong', class_='hv--name')
                        product_name = product_name_tag.get_text() if product_name_tag else "Unknown Product"
                        link_tag = row.find('a', href=True)
                        category_link = link_tag['href'] if link_tag else "Unknown Link"
                        price_tag = row.find('td', class_='hv--price')
                        price = price_tag.a.get_text() if price_tag else "Unknown Price"

                        currency = price[-1] if not price[-1].isdigit() else "Unknown Currency"
                        price = price.replace(',', '.').replace(' ', '')[:-1] if currency != "Unknown Currency" else price

                        

                        if (f"'https://hinta.fi{category_link}'") in str(entry_xl):
                            skipped_items += 1
                        else:
                            entry_xl.append((product_name, price, currency, f"https://hinta.fi{category_link}"))
                            actual_items_amount += 1
                        items_amount += 1
                        progress_callback(items_amount,total_items)
                    if skipped_items != 0:
                        print(f"Just skipped {skipped_items} items")
                    print(f"Progress - > {items_amount}(actual {actual_items_amount}) out of {total_items}")
                    
                    page_number += 1

            except requests.RequestException:
                print("Error - Failed to fetch content after 5 seconds of trying")
                break

        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"{current_time} - The site's listings were updated (from {items_amount_old} to {items_amount})..."
        items_amount_old = items_amount
        columns = ("Item", "Price", "Currency", "Link")
        return entry, entry_xl, items_amount_old, columns
    elif re.match(r'https://hinta\.fi/\d+/.*', website):
        print("Scanning product list (\d+/.*)")
        progress_callback(0,1)

        #entry_xl.append(("↵ Return to the previous page","","","",back_page[back_page_index-2]))

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
        columns = ("Item","Seller","Price","Currency","Link")
        progress_callback(1,1)
        return entry, entry_xl, items_amount_old, columns
    elif "hinta.fi" in website:
        progress_callback(0,1)
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
        progress_callback(1,1)
        return entry, entry_xl, items_amount_old, columns
