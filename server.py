from flask import Flask, request
import hmac
import hashlib
import os
from dotenv import load_dotenv
import base64

load_dotenv()
app = Flask(__name__)

PRODUCT_CREATED_SECRET = os.getenv("PRODUCT_CREATED_WEBHOOK")
PRODUCT_UPDATED_SECRET = os.getenv("PRODUCT_UPDATED_WEBHOOK")

def verify_signature(secret, data, signature):
    if isinstance(data, str):
        data = data.encode('utf-8')
  
    expected_signature = hmac.new(
        secret.encode('utf-8'), data, hashlib.sha256
    ).digest()
    
    expected_signature_base64 = base64.b64encode(expected_signature).decode('utf-8')

    return hmac.compare_digest(expected_signature_base64, signature)


@app.route('/webhook', methods=['POST'])
def webhook():
    raw_data = request.data
    signature = request.headers.get("X-WC-Webhook-Signature")

    if PRODUCT_CREATED_SECRET and verify_signature(PRODUCT_CREATED_SECRET, raw_data, signature):
        print("✅ Product CREATED webhook received")
    elif PRODUCT_UPDATED_SECRET and verify_signature(PRODUCT_UPDATED_SECRET, raw_data, signature):
        print("🔁 Product UPDATED webhook received")
    else:
        print("❌ Invalid webhook signature")
        return "Invalid signature", 403

    os.system("python fetch.py")  
    
    return "Webhook received", 200

@app.route('/run_push', methods=['GET'])
def run_push():
    print("🚀 Push triggered via /run_push")
    os.system("python push.py")
    return "Push started", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
