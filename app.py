from flask import Flask, jsonify, send_file, render_template
import sqlite3
from PIL import Image, ImageDraw, ImageFont
import io
import json
import os

app = Flask(__name__)

# Connect to SQLite database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "nft_metadata.db")
API_URL = "https://api.shibaville.io/ville/image/"
LOGO_FILE = os.path.join(BASE_DIR, "logo.png")
LOGO = img = Image.open(LOGO_FILE)

def fetch_metadata_from_db(nft_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM metadata WHERE id=?", (nft_id,))
    data = cursor.fetchone()
    conn.close()
    if data:
        return {
            "id": data[0],
            "image": API_URL + str(data[0]),
            "region": data[1],
            "location": data[2],
            "attributes": json.loads(data[3])
        }
    return None

def fetch_all_nfts_from_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM metadata order by id asc")
    nft_ids = [row[0] for row in cursor.fetchmany(500)]
    print(nft_ids)
    conn.close()
    return [fetch_metadata_from_db(nft_id) for nft_id in nft_ids if nft_id is not None]



# Route to fetch metadata
@app.route("/ville/<int:nft_id>", methods=["GET"])
def get_metadata(nft_id):
    metadata = fetch_metadata_from_db(nft_id)
    if metadata:
        return jsonify(metadata)
    return jsonify({"error": "NFT not found"}), 404

# Route to generate dynamic image
@app.route("/ville/image/<int:nft_id>", methods=["GET"])
def generate_image(nft_id):
    metadata = fetch_metadata_from_db(nft_id)
    if not metadata:
        return jsonify({"error": "NFT not found"}), 404


    logo = LOGO.resize((300, 300))

    # Create dynamic image
    image = Image.new("RGB", (400, 400), color="white")
    image.paste(logo, (50, 50))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    draw.rectangle((5, 5, 395, 395), outline="black")
    draw.text((10, 10), metadata.get("region", "Unknown"), fill="black", font=font)
    draw.text((10, 20), metadata.get("location", "Unknown"), fill="black", font=font)
    
    y_offset = 60
    for trait in metadata["attributes"]:
        draw.text((10, y_offset), f"{trait['trait']}: {trait['value']}", fill="black", font=font)
        y_offset += 10

    # Save to in-memory file
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    return send_file(img_byte_arr, mimetype="image/png")


@app.route("/")
def home():
    # Get 500 NFTs from the database
    nfts = fetch_all_nfts_from_db()

    return render_template("index.html", nfts=nfts)