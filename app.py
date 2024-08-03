from flask import Flask, request, jsonify, render_template, make_response, session
from werkzeug.exceptions import RequestEntityTooLarge
from flask_session import Session
from apscheduler.schedulers.background import BackgroundScheduler
import secrets
import keras_ocr
from PIL import Image
import numpy as np
import httpx
import uuid
from cs50 import SQL
from datetime import datetime, timezone, timedelta
import os

# Configure application
app = Flask(__name__)

# Limit file size to prevent denial-of-service (DoS) attacks
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB limit

# Enable automatic HTML reloading
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Generate secret key using a 24-character hexadecimal string
app.secret_key = secrets.token_hex(24)

# Note: Perform OCR only in English for now
ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg"]
OCR_MODELS = ["OCR with TensorFlow", "API OCR"]

# Configure CS50 Library to use SQLite database
database_path = os.path.join("database", "ocr-results.db")
db = SQL(f"sqlite:///{database_path}")

# Create table
db.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        datetime DATETIME DEFAULT CURRENT_TIMESTAMP,
        text TEXT NOT NULL,
        UNIQUE (id, user_id, datetime, text)
    );
""")

# Create indexes to facilitate quick selection
db.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON history(user_id);")

# Function to read API key from a text file
def read_api_key(file_path):
    with open(file_path, "r") as file:
        api_key = file.read().strip()
        return api_key

# OCR.space API key
API_KEY = read_api_key("API-and-config/API-key")

# Async function to work with the OCR.space API
async def ocr_space_api(file, overlay=False, api_key="helloworld", language="eng"):
    """ OCR.space API request with "FileStorage" object. """
    payload = {
        "isOverlayRequired": overlay,
        "apikey": api_key,
        "language": language,
        "OCREngine": 2,
    }
    files = {
        "file": (file.filename, file.stream, file.mimetype)
    }
    # Using Python"s async/await syntax with HTTP/2
    async with httpx.AsyncClient(http2=True) as client:
        try:
            # Send request to OCR.space API
            response = await client.post(
                "https://api.ocr.space/parse/image",
                files=files,
                data=payload,
            )
            # Raise an error for bad responses
            response.raise_for_status()

            # Parse and return JSON response
            return response.json()

        # Error handling
        except httpx.HTTPStatusError as e:
            return {"error": "An error occurred while processing the image."}
        except httpx.RemoteProtocolError as e:
            return {"error": "A network error occurred. Please try again later."}
        except Exception as e:
            return {"error": "An unexpected error occurred. Please try again later."}

# Extract text from response
def extract_text_from_api(main_key, text_key, json_response):
    if main_key in json_response and len(json_response[main_key]) > 0:
        text = json_response[main_key][0].get(text_key)
        return text
    return None

# Function to perform OCR
def read_text(np_image):
    model_result = pipeline.recognize([np_image])
    # Concatenate the recognized text
    text_result = " ".join([str(word) for word, _ in model_result[0]])
    return text_result

# Initialize the pipeline for keras_ocr (OCR on server)
pipeline = keras_ocr.pipeline.Pipeline()

# Check file format and its content (return False if not an image and True otherwise)
def check_file(filename, file):
    # Check if file has a supported extension
    if filename.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
        # Check the file content by attempting to open it with PIL
        try:
            with Image.open(file) as img:
                # Verify the image integrity
                img.verify()
            return True
        except (IOError, SyntaxError) as e:
            return False
    return False

# Function to clean expired data in the SQL database
def cleanup_expired_data():
    two_days_ago = datetime.now(timezone.utc) - timedelta(days=2)
    db.execute("DELETE FROM history WHERE datetime < ?;", two_days_ago)

# Configure APScheduler
scheduler = BackgroundScheduler()

# Schedule cleanup to run every hour
scheduler.add_job(func=cleanup_expired_data, trigger="interval", hours=1)
scheduler.start()

# Custom error handler for RequestEntityTooLarge (if file is more than 16 MB)
@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(e):
    return jsonify(
        {"error": "File is too large. The maximum file size is 16MB."}), 413

# Index route
@app.route("/")
def index():
    """ Use cookie to identify user """
    # Check for user_id cookie
    user_id = request.cookies.get("user_id")

    # If user_id cookie does not exist, generate a new one 
    if not user_id:
        # Generate a random Universally Unique Identifier (UUID)
        user_id = str(uuid.uuid4())
        # Save user id in the session
        session["user_id"] = user_id
        new_user = True
    else:
        new_user = False
        # Save user id in the session
        session["user_id"] = user_id

    # Prepare response
    response = make_response(render_template("index.html", ocr_models=OCR_MODELS))

    # Set user_id cookie if it"s a new user or if the cookie doesn"t exist
    if new_user:
        # Cookie expires after 2 days
        expires = datetime.now(timezone.utc) + timedelta(days=2)
        response.set_cookie(
            "user_id", user_id, expires=expires, secure=True, httponly=True, samesite="Strict")

    return response

# Route to delete user cookies and user data stored
@app.route("/delete", methods=["POST"])
def delete():
    # Ensure it"s a POST request
    if request.method == "POST":
        # Get user id
        user_id = session.get("user_id")

        if not user_id:
            return jsonify({"info": "Already removed user data."})

        try:
            # Remove user_id from session
            session.pop("user_id", None)

            # Remove all the data of this user
            db.execute("DELETE FROM history WHERE user_id = ?", user_id)

            # Prepare JSON response 
            response = jsonify({"message": "Data and cookie deleted"})
            # Delete user_id cookie by setting it to expire immediately
            response.set_cookie("user_id", "", expires=0)
        except Exception as e:
            print(f"Error deleting data: {e}")
            response = jsonify({"error": "Could not remove data."})

        return response

    return jsonify({"error": "Bad request. Use POST request"}), 400

# Route to get result
@app.route("/results", methods=["POST"])
def results():
    # Ensure it"s a POST request
    if request.method == "POST":
        # Query OCR results for this user
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"info": "No user id."})
        ocr_results = db.execute("SELECT datetime, text FROM history WHERE user_id = ?;", user_id)
        return jsonify(ocr_results)

    return jsonify({"error": "Bad request. Use POST request"}), 400

# Submit file route
@app.route("/submit", methods=["POST"])
async def submit():
    # Ensure it"s a POST request
    if request.method == "POST":
        file = request.files.get("file")
        ocr_model = request.form.get("ocrModel")
        user_id = session.get("user_id")

        # Ensure that file exists
        if not file:
            return jsonify({"error": "Please provide a file"}), 400

        # Ensure that ocr_model exists
        if not ocr_model:
            return jsonify({"error": "Please choose an OCR model"}), 400

        # Check file format and its content 
        if not check_file(filename=file.filename, file=file.stream):
            return jsonify({"error": f"The file format is not supported. Supported formats: {tuple(ALLOWED_EXTENSIONS)}"}), 400

        # If user chose server OCR, perform OCR using keras_ocr
        if ocr_model == OCR_MODELS[0]:
            # Try to read image
            try:
                with Image.open(file.stream) as img:
                    # Ensure the image is RGB
                    img = img.convert("RGB")
                    np_img = np.array(img)

                    # Perform OCR
                    ocr_result = read_text(np_img)

                    if not ocr_result:
                        return jsonify({"ocr_result": "No text on the image"})
                    
                # Save the result in the Database
                if user_id and ocr_result:
                    db.execute("INSERT INTO history (user_id, text) VALUES (?, ?);", user_id, ocr_result)
                return jsonify({"ocr_result": ocr_result})

            except Exception as e:
                print(f"Error processing image: {e}")
                return jsonify({"error": "Could not process the image."}), 400

        # If user chose API, send image to ocr.space
        elif ocr_model == OCR_MODELS[1]:
            try:
                # Perform OCR using OCR.space API with URL
                ocr_result = await ocr_space_api(file)

                # Check if OCR result contains an error
                if "error" in ocr_result:
                    return jsonify(ocr_result), 400

                # Get the text
                text = extract_text_from_api(
                    main_key="ParsedResults",
                    text_key="ParsedText",
                    json_response=ocr_result
                )

                # Ensure that the API detected text
                if not text:
                    return jsonify({"ocr_result": "No text on the image"})

                # Save the result in Database
                if user_id and text:
                    db.execute("INSERT INTO history (user_id, text) VALUES (?, ?);", user_id, text)
                return jsonify({"ocr_result": text})

            except Exception as e:
                print(f"Error processing image with API: {e}")
                return jsonify({"error": "Could not process the image."}), 400

    return jsonify({"error": "Invalid request method."}), 500

# Handle application startup and shutdown
if __name__ == "__main__":
    # Run cleanup immediately on startup
    cleanup_expired_data()
    try:
        # Setup automatic reloading (only for development)
        app.run(debug=False, use_reloader=True)
    except (KeyboardInterrupt, SystemExit):
        # Shut down APScheduler when the application is stopped
        scheduler.shutdown()
