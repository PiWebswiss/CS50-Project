from flask import Flask, request, jsonify, render_template
from werkzeug.exceptions import RequestEntityTooLarge
import secrets
import keras_ocr
from PIL import Image
import numpy as np
import requests
import httpx
import logging
import asyncio


# Configure application
app = Flask(__name__)

# Limation file size to limit denial-of-service (DoS) attacks
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
# Generate secret key with 24-character hexadecimal string
app.secret_key = secrets.token_hex(24)

 # To remove !!
""" Note: I will perform OCR only in English  """ 
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif', 'pdf']
OCR_MODELS = ["OCR on server", "API OCR"]


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

            # Parse and return JSON responce
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

# Extract text from responce
def extract_text_from_api(main_key, text_key, json_responce):
    if main_key in json_responce and len(json_responce[main_key]) > 0:
        text = json_responce[main_key][0].get(text_key)
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

# Custom erro handler for RequestEntityTooLarge (if file is more than 16 MP)
@app.errorhandler(RequestEntityTooLarge)
def handle_large_file():
    return jsonify(
        {"error": "File is too large. The maaximun file size is 16MB."}), 413


# Intex route
@app.route("/")
def index():
    return render_template("index.html", ocr_models=OCR_MODELS)

# submite file route
@app.route("/submit", methods=["POST"])
async def submit():
    # Ensure it's a POST request
    if request.method == "POST":
        file = request.files.get("file")
        ocr_model = request.form.get("ocrModel")

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
            
                return jsonify({"ocr_result": ocr_result})
            
            except:
                return jsonify({"error": "Could not prosses the image."}), 400
        
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
                    json_responce=ocr_result
                    )
                
                # Ensure that the API detected text
                if not text:
                    return jsonify({"ocr_result": "No text on the image"})
                
                # Return text detected
                return jsonify({"ocr_result": text})

            except:
                jsonify({"error": "Could not prosses the image."}), 400
    
    return jsonify({"error": "Invalid request method."}), 500


""" Run flask: flask --app app.py --debug run  """