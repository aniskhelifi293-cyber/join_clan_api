# api/index.py

from flask import Flask, request, jsonify
from ff_client import FreeFireClient
import logging

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

BOT_UID = "4259358643"
BOT_PASSWORD = "54947EAD7CB497987057DED74F0F4E499DD414D4F126781F0BC243B0EC2E5CF7"

client = None

def initialize_client():
    global client
    try:
        logging.info("🚀 جارٍ تهيئة عميل Free Fire...")
        client = FreeFireClient(BOT_UID, BOT_PASSWORD)
        
        # --- السطر الجديد للتحقق ---
        logging.info(f"Payload check: {client.get_payload_debug_info()}")
        # --------------------------

        client.authenticate()
        logging.info("✅ تم الحصول على التوكن والعميل جاهز!")
    except Exception as e:
        client = None
        logging.error(f"❌ فشل في تهيئة العميل: {e}", exc_info=True)

initialize_client()

# ... (بقية الكود في index.py يبقى كما هو) ...
@app.route('/')
def home():
    return "Anis X-Info API is running. Use /xInFo?u={uid} to get player data.", 200

@app.route('/xInFo', methods=['GET'])
def get_player_info():
    global client
    player_uid = request.args.get('u')

    if not player_uid or not player_uid.isdigit():
        return jsonify({"error": "Bad Request", "message": "Valid Player UID 'u' is required."}), 400

    if not client or not client.is_authenticated():
        logging.warning("⚠️ العميل غير جاهز، محاولة إعادة المصادقة...")
        initialize_client()
        if not client:
            return jsonify({"error": "Service Unavailable", "message": "The info service is temporarily down. Please try again later."}), 503

    try:
        player_data = client.get_player_info(int(player_uid))
        if player_data.get("error"):
             return jsonify(player_data), 404
        
        player_data['api_developer'] = "Anis"
        return jsonify(player_data)
    except Exception as e:
        logging.error(f"Error processing UID {player_uid}: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred."}), 500

if __name__ == "__main__":
    app.run(debug=False)
