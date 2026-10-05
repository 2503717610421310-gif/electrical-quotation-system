import os
import time
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
import database

app = Flask(__name__, static_folder=".")

# Configure local image upload directory
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize SQLite database on startup
database.init_db()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ============================================================
# API ENDPOINTS
# ============================================================

@app.route("/api/upload", methods=["POST"])
def upload_image():
    if "image" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{int(time.time())}_{filename}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
        file.save(filepath)

        image_url = f"/uploads/{unique_filename}"
        return jsonify({"success": True, "image_url": image_url})

    return jsonify({"error": "Invalid file extension"}), 400


@app.route("/api/settings", methods=["GET"])
def get_settings():
    try:
        settings = database.get_settings()
        return jsonify(settings)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/catalog", methods=["GET", "POST"])
def handle_catalog():
    if request.method == "POST":
        try:
            data = request.get_json()
            item_id = database.add_catalog_item(
                name=data.get("name"),
                category=data.get("category"),
                description=data.get("description", ""),
                unit=data.get("unit"),
                rate=data.get("rate"),
                gst=data.get("gst", 18),
                image_url=data.get("image_url", ""),
            )
            return jsonify({"success": True, "id": item_id})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        try:
            catalog = database.get_catalog()
            return jsonify(catalog)
        except Exception as e:
            return jsonify({"error": str(e)}), 500


@app.route("/api/next_number", methods=["GET"])
def get_next_number():
    try:
        doc_type = request.args.get("type", "quotation")
        doc_number = database.get_next_doc_number(doc_type)
        return jsonify({"doc_number": doc_number})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents", methods=["POST"])
def create_document():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid payload"}), 400

        data["is_gst"] = bool(data.get("is_gst", True))
        doc_id = database.save_document(data)
        document = database.get_document(doc_id)
        return jsonify({"success": True, "id": doc_id, "document": document})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/<int:doc_id>", methods=["GET"])
def get_document(doc_id):
    try:
        document = database.get_document(doc_id)
        if document is None:
            return jsonify({"error": "Document not found"}), 404
        return jsonify(document)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/<int:doc_id>/convert", methods=["POST"])
def convert_document(doc_id):
    try:
        invoice_id = database.convert_quotation_to_invoice(doc_id)
        document = database.get_document(invoice_id)
        return jsonify({"success": True, "invoice_id": invoice_id, "document": document})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)