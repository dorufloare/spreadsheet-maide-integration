# filepath: c:\Users\doruf\info\work\maide\product_spreadsheet\main.py
from woocommerce import API
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
from pprint import pprint
import os

# Load environment variables from .env file
load_dotenv()

# Connect to WooCommerce API
wcapi = API(
    url=os.getenv("URL"),
    consumer_key=os.getenv("CONSUMER_KEY"),
    consumer_secret=os.getenv("CONSUMER_SECRET"),
    version="wc/v3",
    timeout=30
)

# Connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("your-credentials.json", scope)
client = gspread.authorize(creds)

spreadsheet = client.open_by_key(os.getenv("SPREADSHEET_KEY"))
sheet = spreadsheet.sheet1 

# Fetch data from the sheet
data = sheet.get_all_values()

# Extract headers
headers = data[0]
rows = data[1:]  # Remove header row

header_map = {headers[i]: i for i in range(len(headers))}

row_index = 0
    
while row_index < len(rows):
    row = rows[row_index]
    product_id = row[header_map["Id"]].strip()
    product_name = row[header_map["Name"]].strip()
    product_price = row[header_map["Price"]].strip()
    product_sku = row[header_map["SKU"]].strip()
    product_type = row[header_map["Type"]].strip()
    thumbnail_url = row[header_map["Image"]].strip() if row[header_map["Image"]] != "No Image" else None
    tiered_pricing = row[header_map["Fixed Tiered Prices"]].strip()
    short_description = '<p> .checkmark {font-weight: bold;  margin-top: 0px;margin-bottom: 0px;}.light-text {font-weight: normal;font-size: smaller;color: #888;</p>\n<p class="checkmark" style="margin-top: 20px">✓ PLATA LA LIVRARE</p>\n<p class="light-text">platesti la livrarea coletului</p>\n<p class="checkmark">✓ VERIFICARE COLET</p>\n<p class="light-text">la solicitarea clientului</p>\n<p class="checkmark">✓ RETUR IN 14 DE ZILE</p>\n<p class="light-text">garantat banii inapoi</p>\n'
    product_ean = row[header_map["EAN"]].strip()
    meta_data = [ {"key": "_alg_ean", "value": product_ean} if product_ean else None ]
    
    if product_type == "variation":
        # Skip variations for now
        row_index += 1
        continue
    
    update_data = {
        "name": product_name,
        "sku": product_sku,
        "type": product_type,
        "regular_price": str(product_price),
        "images": [{"src": thumbnail_url}] if thumbnail_url else [],
        "tiered_pricing_fixed_rules": tiered_pricing,
        "short_description": short_description,
        "meta_data": meta_data,
    }
    
    #pprint(update_data)

    # Update existing product
    if product_id:
        response = wcapi.get(f"products/{product_id}")	
        if response.status_code == 200:
            existing_product = response.json()
            
            for key in update_data:
                if update_data[key]:
                    existing_product[key] = update_data[key]
            
            response = wcapi.put(f"products/{product_id}", existing_product)
            if response.status_code == 200:
                print(f"Product {product_id} updated successfully.")
            else:
                print(f"Failed to update product {product_id}. Status code: {response.status_code}")
        else:
            print(f"Product {product_id} not found. Status code: {response.status_code}")
            
    else:
        # Create new product
        response = wcapi.post("products", update_data)
        if response.status_code == 201:
            print(f"Product {product_name} created successfully.")
        else:
            print(f"Failed to create product {product_name}. Status code: {response.status_code}")
   
    if product_type == "variable":
        variation_response = wcapi.get(f"products/{product_id}/variations")
        existing_variations = variation_response.json()

        existing_variations_names = set()

        for variation in existing_variations:
            existing_variations_names.add(product_name + " - " + variation["attributes"][0]["option"])
        
        initial_row_index = row_index + 1
        row_index += 1
        while row_index < len(rows):
            v_row = rows[row_index]
            variation_sku = v_row[header_map["SKU"]].strip()
            
            if not variation_sku.startswith(product_sku):
                break
            
            variation_price = v_row[header_map["Price"]].strip()
            variation_name = v_row[header_map["Name"]].strip()
            variation_id = v_row[header_map["Id"]].strip()  
            variation_tiered_pricing = v_row[header_map["Fixed Tiered Prices"]].strip()
            
            variation_data = {
                "regular_price": str(variation_price),
                "name": variation_name,
                "sku": variation_sku + "-" + str(row_index - initial_row_index),
                "tiered_pricing_fixed_rules": variation_tiered_pricing,
                "short_description": short_description,
                "meta_data": meta_data,
            }        
            
            #pprint(variation_data)    
            
            # Update existing variation
            if variation_name in existing_variations_names:
                existing_variation = wcapi.get(f"products/{product_id}/variations/{variation_id}").json()
                for key in variation_data:
                    if variation_data[key]:
                        existing_variation[key] = variation_data[key]
                        
                response = wcapi.put(f"products/{product_id}/variations/{variation_id}", existing_variation)
                print(response.json())
                if response.status_code == 200:
                    print(f"Variation {variation_id} updated successfully.")
                else:
                    print(f"Failed to update variation {variation_id}. Status code: {response.status_code}")
                    
            else:
                respone = wcapi.post(f"products/{product_id}/variations", variation_data)
                if response.status_code == 201:
                    print(f"Variation {variation_name} created successfully.")
                else:
                    print(f"Failed to create variation {variation_name}. Status code: {response.status_code}")

    row_index += 1