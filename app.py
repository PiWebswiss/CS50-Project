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

# Limation file size to limit denial-of-service (DoS) attacks
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Generate secret key with 24-character hexadecimal string
app.secret_key = secrets.token_hex(24)



""" Note: I will perform OCR only in English  """ 
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']
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

# Create indexs to facilitate quick select
db.execute("CREATE INDEX IF NOT EXISTS idx_user_id On history(user_id);")


# Fontion to read API key from text file
def read_api_key(file_path):
    with open(file_path, "r") as file:
        api_key = file.read()
        return api_key
    
# OCR.space API key
API_KEY = read_api_key("API-and-config/API-key")
""" API key OCR.space Online OCR (free) https://ocr.space/OCRAPI """

# Async function to work with the OCR.space API
# Modified code from https://github.com/Zaargh/ocr.space_code_example/blob/master/ocrspace_example.py
async def ocr_space_api(file, overlay=False, api_key='helloworld', language='eng'):
    """ OCR.space API request with 'FileStorage' object. """

    payload = {'isOverlayRequired': overlay,
               'apikey': api_key,
               'language': language,
               'OCREngine': 2,
               }
    files = {
        'file': (file.filename, file.stream, file.mimetype)
    }
    # Uisng Python's async/await syntax with HTTP/2
    async with httpx.AsyncClient(http2=True) as client:
        try:
            # Send request to OCR.space API
            response = await client.post('https://api.ocr.space/parse/image',
                            files=files,
                            data=payload,
                            )
            # Raise an error for bad responses
            response.raise_for_status()

            # Parse and return JSON response
            return response.json()
        
        # Error handling
        except httpx.HTTPStatusError as e:
            # Log detailed error
            print(f"Request error occurred {e}")
            return {"error": "An error occurred while processing the image"}
        except httpx.RemoteProtocolError as e:
            print(f"HTTP error occurred: {e}")
            return {"error": "A network error occured. Please try again later."}
        except Exception as e:
            print(f"An unexpcted erro occurred: {e}")
            return {"error": "An unexpcted erro occurred. Please try again later."}

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
""" https://github.com/faustomorales/keras-ocr?tab=readme-ov-file """

# Check file format
def check_format(filename):
    return filename.lower().endswith(tuple(ALLOWED_EXTENSIONS))

# Configurate APScheduler
scheduler = BackgroundScheduler()

# Function to clean expired data in the SQL database
def cleanup_expired_data():
    two_days_ago = datetime.now(timezone.utc) - timedelta(days=2)
    db.execute("DELECT FROM history WHERE datetime < ?;", two_days_ago)

# Schedule cleanup to run every hour
scheduler.add_job(func=cleanup_expired_data, trigger="interval", hours=1)
scheduler.start()

# Custom error handler for RequestEntityTooLarge (if file is more than 16 MP)
@app.errorhandler(RequestEntityTooLarge)
def handle_large_file():
    return jsonify(
        {"error": "File is too large. The maximum file size is 16MB."}), 413


# Intex route
@app.route("/")
def index():
    """ using cookie to indientify user """
    # Check for user_id cookie
    user_id = request.cookies.get("user_id")
    print("USER_ID", user_id)

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
    print("SESSTION USER_ID", session.get("user_id"))

    """ TO DO REMOVE ALL USER DATA AFTER 2 DAYS """

    # Prepare response
    response = make_response(render_template("index.html", ocr_models=OCR_MODELS))
    

    # Set user_id cookie if it's a new user or if the cookie doesn't exist
    if new_user:
        # Cookie expires after 2 days
        expires = datetime.now(timezone.utc) + timedelta(days=2)
        response.set_cookie(
            "user_id", user_id, expires=expires, secure=True, httponly=True, samesite="Strict")

    return response

@app.route("/results", methods=["POST"])
def get_results():
    # Ensure it's a POST request
    if request.method == "POST":
        # Query OCR results for this user
        user_id = session.get("user_id") 
        if not user_id:
            return jsonify({"info": "No user id."})
        ocr_results = db.execute("SELECT datetime, text FROM history WHERE user_id = ?;", user_id)
        print("ocr_results", ocr_results)
        """ Note: ocr_results is a dict key: datetime and text """
        return jsonify(ocr_results)
    
    return jsonify({"error": "Bad request. Use POST request"})


# submite file route
@app.route("/submit", methods=["POST"])
async def submit():
    # Ensure it's a POST request
    if request.method == "POST":
        file = request.files.get("file")
        ocr_model = request.form.get("ocrModel")
        user_id = session.get("user_id")

        # Ensure that file exists
        if not file:
            return jsonify({"error": "Please provide a file"}), 400
        
         # Ensure that ocr_model exists
        if not ocr_model:
            return jsonify({"error": "Please chose a OCR model"}), 400
        
        # Check file extension is a supported one
        if not check_format(file.filename):
            return jsonify({"error": f"The file format is not supported. Supported formats: {tuple(ALLOWED_EXTENSIONS)}"}), 400
        
        # If user chose server OCR then we perfome OCR using keras_ocr
        if ocr_model == OCR_MODELS[0]:

            # Try to read image
            try:
                with Image.open(file.stream) as img:
                    # Ensure the image is RGB
                    img = img.convert("RGB")
                    np_img = np.array(img)

                    # Perform OCR
                    ocr_result = read_text(np_img)

                    if ocr_result == "":
                        return jsonify({"ocr_result": "No text on the image"})
                # Save the result in Database
                if user_id and ocr_result:
                    db.execute("INSERT INTO history (user_id, text) VALUES (?, ?);", user_id, ocr_result)
                return jsonify({"ocr_result": ocr_result})
            
            except:
                return jsonify({"error": "Could not process the image."}), 400
        
        # If user chose API send image to ocr.space
        elif ocr_model == OCR_MODELS[1]:
            try:
            
                # Perfrom OCR using OCR.space API with URL
                ocr_result = await ocr_space_api(file)

                # Check if OCR result contains an error
                if "error" in ocr_result:
                    return jsonify(ocr_space_api), 400
               
                # Get the text
                text = extract_text_from_api(
                    main_key="ParsedResults", 
                    text_key="ParsedText",
                    json_response=ocr_result
                    )
                
                # Ensure that the API detected text
                if not text:
                    return jsonify({"ocr_result": "No text on the image"})
                
                # Return text detected
                # Save the result in Database
                if user_id and text:
                    db.execute("INSERT INTO history (user_id, text) VALUES (?, ?);", user_id, text)
                return jsonify({"ocr_result": text})

            except:
                jsonify({"error": "Could not process the image."}), 400
    
    return jsonify({"error": "Invalid request method."}), 500

if __name__ == "__name__":
    # Rune cleanup immadiately on startup
    cleanup_expired_data()
    try:
        # Start the Flask in debug model (remove for production use)
        app.run(debug=True)
    except (KeyboardInterrupt, SystemExit):
        # Shut down APScheduler when the application is stopped
        scheduler.shutdown()

""" Run flask: flask run """