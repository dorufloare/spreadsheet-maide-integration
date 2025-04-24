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

# Fetch products from WooCommerce
page = 1
all_products = []
while True:
    response = wcapi.get(f"products", params={"per_page": 10, "page": page})
    products = response.json()
    if not products:  # Stop if no more products on the page
        break	
    
    all_products.extend(products)
    page += 1

# Extract required attributes
data = [["Id", "SKU", "EAN", "Type", "Name", "Price", "Fixed Tiered Prices", "Image"]]  # Header
for product in all_products:
    try:    
        thumbnail_url = str(product["images"][0]["src"]) if product["images"] else "No Image"
    except IndexError:
        thumbnail_url = "No Image"
    except KeyError:
        thumbnail_url = "No Image"
    except TypeError:
        thumbnail_url = "No Image"
    except AttributeError:
        thumbnail_url = "No Image"	
    
    try:
        ean_value = next((item['value'] for item in product['meta_data'] if item['key'] == '_alg_ean'), None)
    except: 
        ean_value = None
        
    data.append([
        product["id"], 
        product["sku"],
        ean_value,
        product["type"],
        product["name"], 
        product["price"], 
        str(product["tiered_pricing_fixed_rules"]),
        thumbnail_url,
    ])

    if product["type"] == "variable":
        for variation in product["variations"]:
            variation_response = wcapi.get(f"products/{product['id']}/variations/{variation}").json()
            
            data.append([
                variation_response["id"],
                variation_response["sku"],
                ean_value,
                "variation",
                str(product["name"] + " - " + variation_response["attributes"][0]["option"]),
                variation_response["price"],
                str(variation_response["tiered_pricing_fixed_rules"]),
                thumbnail_url,
            ])
            
 
    #pprint(data)
 

print("Data fetched successfully.")

# Connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("your-credentials.json", scope)
client = gspread.authorize(creds)

spreadsheet = client.open_by_key(os.getenv("SPREADSHEET_KEY"));
sheet = spreadsheet.sheet1 
sheet.update("A1", data)

