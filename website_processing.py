import datetime
import json
from bs4 import BeautifulSoup
import re
import requests


def process_website_content(website,content,items_amount_old, website_content_listbox,progress_callback,edit_back_page,stop_scan,debug,stop_flag,redirect):
    global back_page_index,back_page
    debug.d_print("Identifying the website")
        
    if "hinta.fi" in website:
        debug.d_print("Hinta.fi identified")
        entry, entry_xl, items_amount_old, columns = hinta_process_website_content(website,content,items_amount_old, website_content_listbox,progress_callback,stop_flag,stop_scan,debug)
    elif "hintaopas.fi":
        debug.d_print("Hintaopas.fi identified")
        entry, entry_xl, items_amount_old, columns = hintaopas_process_website_content(website,content,items_amount_old, website_content_listbox,progress_callback,stop_flag,stop_scan,debug)
    if redirect == False:
        edit_back_page(website)
    
    return entry, entry_xl, items_amount_old, columns

def hinta_process_website_content(website,content,items_amount_old, website_content_listbox,progress_callback,stop_flag,stop_scan,debug):

    items_amount = 0
    entry_xl = []
    soup = BeautifulSoup(content, 'html.parser')
    script_tags = soup.find_all('script', type='application/ld+json')

    if "hinta.fi/g" in website:
        debug.d_print("Scanning category list (/g)")

        total_items_element = soup.find('span', class_='hv-text-strong')
        if total_items_element:
            total_items = int(total_items_element.text.replace(',', '.').replace(' ', ''))
        else:
            total_items = 15 # Failback
        debug.d_print(f"The amount of expected elements is {total_items_element}")

        items_amount = 0
        actual_items_amount = 0
        page_number = 1
        scan = True

        while scan:
            try:

                if stop_scan():
                    scan = False
                    debug.d_print("Received stop_scan, perfoming last scan")
                skipped_items = 0
                if items_amount == total_items:
                    debug.d_print(f"Exiting job in total_amount({items_amount} == {total_items})")
                    items_amount = actual_items_amount
                    break
                if stop_flag:
                    if page_number == stop_flag+1:
                        debug.d_print(f"Exiting job on stop_flag({page_number} == {stop_flag+1})")
                        progress_callback(total_items,total_items)
                        items_amount = actual_items_amount
                        break                   
                debug.d_print(f"Trying to get page {page_number}: {website}?l=1&p={page_number}","-->",True)
                response = requests.get(f"{website}?l=1&p={page_number}", timeout=5)
                debug.d_print(f"Got response {response.status_code}","\n",False)
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
                        if stop_flag:
                            progress_callback(page_number,stop_flag)
                        else:
                            progress_callback(items_amount,total_items)
                    if skipped_items != 0:
                        debug.warning_print(f"Just skipped {skipped_items} items","W")
                    debug.d_print(f"Progress - > {items_amount}(actual {actual_items_amount}) out of {total_items}")
                    
                    page_number += 1

            except requests.RequestException:
                debug.warning_print("Failed to fetch content after 5 seconds of trying","E")
                break

        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"{current_time} - The site's listings were updated (from {items_amount_old} to {items_amount})..."
        items_amount_old = items_amount
        columns = ("Item", "Price", "Currency", "Link")
        return entry, entry_xl, items_amount_old, columns
    elif re.match(r'https://hinta\.fi/\d+/.*', website):
        debug.d_print("Scanning product list (\d+/.*)")
        progress_callback(0,1)

        for script in script_tags:
            try:
                product_data = json.loads(script.string)
                if "@type" in product_data and product_data["@type"] == "Product":
                    product_name = product_data["name"] if "name" in product_data else "Unknown Product"
                    
                    if "offers" in product_data:
                        if "@type" in product_data["offers"] and product_data["offers"]["@type"] == "AggregateOffer":
                            offers = product_data["offers"].get("offers", [])
                        else:
                            offers = [product_data["offers"]]
                    for offer in offers:
                        offer_name = offer.get("name", "Unknown Offer")
                        price = offer.get("price", "Unknown Price")
                        currency = offer.get("priceCurrency", "EUR")
                        seller_name = offer.get("seller", {}).get("name", "Unknown Seller")

                        entry = f"Item: {product_name} Offer: {offer_name} Price: {price} {currency} Seller: {seller_name}"
                        entry_xl.append((offer_name, seller_name , price, currency))
                        items_amount += 1
            except json.JSONDecodeError as e:
                debug.warning_print("JSON Decode Error:","W")
                debug.warning_print(f"{e}","E")
                pass  # Skip this script if it's not valid JSON
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"{current_time} - The site's listings were updated (from {items_amount_old} to {items_amount})..."
        items_amount_old = items_amount
        columns = ("Item","Seller","Price","Currency","Link")
        progress_callback(1,1)
        return entry, entry_xl, items_amount_old, columns
    elif "hinta.fi" in website:
        progress_callback(0,1)
        debug.d_print("Scanning main page")
        category_links = soup.find_all('a', class_='hv-menu-i-a')
        entry_xl = []

        for link in category_links:
            category_name = link.text
            category_link = link['href']
            
            # Check if the link contains unwanted patterns, skip if it does
            if "hv-store-logo-w" in link.parent.attrs.get("class", []) or "kauppaan.php" in category_link:
                continue
            
            # Replace spaces with an underscore
            category_name_fixed = " ".join(category_name.split())
            
            entry_xl.append((category_name_fixed, "https://hinta.fi" + category_link))
            items_amount += 1

        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"{current_time} - The site's listings were updated (from {items_amount_old} to {items_amount})..."
        
        items_amount_old = items_amount
        items_amount = len(entry_xl)
        columns = ("Category", "Link")
        progress_callback(1,1)
        return entry, entry_xl, items_amount_old, columns

def hintaopas_process_website_content(website, content, items_amount_old, website_content_listbox, progress_callback, stop_flag, stop_scan, debug):
    items_amount = 0
    entry_xl = []
    soup = BeautifulSoup(content, 'html.parser')
    script_tags = soup.find_all('script', type='application/ld+json')
    
    if re.match(r'^https://hintaopas\.fi/product\.php\?p=\d+$',website):
        debug.d_print("Scanning product list")
        progress_callback(0,1)
        anchor_tags = soup.find_all('a', class_='ExternalLink-sc-1ap2oa8-2')
        for tag in anchor_tags:
            try:
                store = tag.find('span', class_='StoreInfoTitle-sc-bc2k22-1').text.strip()
                item = tag.find('span', class_='StyledProductName-sc-1v7pabx-2').text.strip()
                price = tag.find('h4', class_='PriceLabel-sc-lboeq9-0').text.strip()
                price = float(re.sub("[^0-9,.]", "", price).replace(',', '.'))
                link = tag['href']
                rating_container = tag.find('div', class_='RatingContainer-sc-u1xymf-0')
                rating = rating_container['data-rating'] if rating_container else 'N/A'
                entry_xl.append((store,rating,item,price,link))
                items_amount += 1
            except:
                pass
        items_amount_old = items_amount
        columns = ("Store","Store's Rating","Item", "Price", "Link")
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"{current_time} - The site's listings were updated (from {items_amount_old} to {items_amount})..."
        progress_callback(1,1)
        return entry, entry_xl, items_amount_old, columns
    elif re.match(r'^https://hintaopas\.fi/c/[^?]+\?brand=\d+$', website):
        debug.d_print("Scanning brand list")
        debug.d_print("Trying to get data using the the first way")
        progress_callback(0,1)
        table_rows = soup.find_all('tr', class_='Tr-sc-1stvbsu-2 chMRiA')
        for row in table_rows:
            product_link = row.find('a', class_='InternalLink-sc-1ap2oa8-1')
            item = product_link.find('h3', class_='ProductNameTable-sc-1stvbsu-3').text.strip()
            price_element = row.find('span', class_='PriceLabel-sc-lboeq9-0')
            price = price_element.text.strip()
            price = float(re.sub("[^0-9,.]", "", price).replace(',', '.'))
            link = product_link['href']
            entry_xl.append((item,price, "https://hintaopas.fi" + link))
            items_amount += 1
        if items_amount == 0:
            debug.warning_print("Got 0 items from the first scan, perfoming product scan instead","W")
            list_items = soup.find_all('li', attrs={'data-test': 'ProductGridCard'})
            for item in list_items:
                product_link = item.find('a', class_='InternalLink-sc-1ap2oa8-1')
                name = product_link.find('span', class_='Text--j47ncs khWbVp titlesmalltext').text.strip()
                price_element = item.find('span', class_='Text--j47ncs iolWON')
                price = price_element.text.strip()
                price = float(re.sub("[^0-9,.]", "", price).replace(',', '.'))
                link = product_link['href']
                entry_xl.append((name,price, "https://hintaopas.fi" + link))
                items_amount += 1

        items_amount_old = items_amount
        columns = ("Item", "Price", "Link")
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"{current_time} - The site's listings were updated (from {items_amount_old} to {items_amount})..."
        progress_callback(1,1)
        return entry, entry_xl, items_amount_old, columns
    elif re.match(r'https://hintaopas\.fi/c/.*', website):
        debug.d_print("Scanning category list")
        progress_callback(0,1)
        entry_data = soup.find_all('li', style='flex:0 0 110px')

        for data in entry_data:
            link_element = data.find('a', class_='InternalLink-sc-1ap2oa8-1')
            name_element = data.find('span', class_='Text--j47ncs gEcihA titlesmalltext')
            if link_element and name_element:
                item = name_element.text.strip()
                link = link_element['href']
                entry_xl.append((item,"https://hintaopas.fi" + link))
                items_amount += 1
        columns =("Category","Link")

        if items_amount == 0:
            debug.warning_print("Got 0 items from the first scan, perfoming item scan instead","W")
            entry_data = soup.find_all('tr', class_='Tr-sc-1stvbsu-2 chMRiA')
            for data in entry_data:
                item = data.find('h3', class_='ProductNameTable-sc-1stvbsu-3').text.strip()
                price_element = data.find('span', class_='PriceLabel-sc-lboeq9-0')
                price = price_element.text.strip() if price_element else ""
                price = float(re.sub("[^0-9,.]", "", price).replace(',', '.'))
                link_element = data.find('a', class_='InternalLink-sc-1ap2oa8-1')
                link = link_element['href'] if link_element else ""
                entry_xl.append((item,price,"https://hintaopas.fi" + link))
                items_amount += 1
            columns =("Category","Price","Link")
        items_amount_old = items_amount
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"{current_time} - The site's listings were updated (from {items_amount_old} to {items_amount})..."
        progress_callback(0,1)
        return entry, entry_xl, items_amount_old, columns

    elif "hintaopas.fi" in website:
        debug.d_print("Scanning main page")
        progress_callback(0,1)
        list_items = soup.find_all('li', class_='SubLevelItem-sc-1niqwua-6 cLkuDP')
        for item in list_items:
            name = item.a.text
            link = item.a['href']
            entry_xl.append((name, "https://hintaopas.fi" + link))
            items_amount += 1
        
        items_amount_old = items_amount
        columns =("Category", "Link")
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"{current_time} - The site's listings were updated (from {items_amount_old} to {items_amount})..."
        progress_callback(1,1)
        return entry, entry_xl, items_amount_old, columns
