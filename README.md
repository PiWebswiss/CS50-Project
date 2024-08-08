# Web OCR Application

#### Video Demo

YouTube link: [Demo video](https://youtu.be/dpf1IfWXtRc)

Due to the lack of a good microphone, I used the OpenAI API to read the text for me. Big thanks to the OpenAI API! :)

#### Description

My project is a web application for performing Optical Character Recognition (OCR) using different methods. It provides a user interface to upload images, processes the images on the server side, and returns the predicted text. You can choose between two different methods to perform OCR, **currently available only in English**:

1. **Using TensorFlow with `keras_ocr`**: This is an open-source OCR library that uses TensorFlow. The model runs on the server. For more details, see the [keras-ocr documentation](https://keras-ocr.readthedocs.io/) and the [GitHub repository](https://github.com/faustomorales/keras-ocr).
   - Currently, I am using a pre-trained model, which provides acceptable accuracy in most cases. However, it still requires additional training and fine-tuning to achieve better results, which is on my to-do list.
   - To improve the results of `keras_ocr` and make the text more human-readable, I defined a class with methods to enhance the text output. Most of the code in the class named `Keras_OCR` is copied from a GitHub repository published by shegocodes. Here is a link to the [GitHub Jupyter Notebook](https://github.com/shegocodes/keras-ocr/blob/main/Keras-OCR.ipynb).
   - I’m still encountering some unwanted results from `Keras_OCR`, so further fine-tuning or retraining is needed to achieve more accurate outcomes.
   - I integrated a deep learning model to ensure that user images are processed on my server, guaranteeing that no images are saved and that the processing is secure. This avoids sending data to a cloud-based service, where we may not know how the images are processed. I recommend using `OCR with TensorFlow` for tasks where security is a concern.

2. **Using the OCR Space API**: This is a cloud-based OCR service that processes images and returns the text with very good accuracy using their OCR Engine 2. You can find more information about the [OCR Space API](https://ocr.space/ocrapi).
   - The OCR Space API is my default model as it is the most accurate and fast.
   - My server receives and sends your image to the OCR Space API using HTTP/2. I use asynchronous operations with `async/await` in Python so my code can pause execution while waiting for tasks to complete.
   - The API responds with JSON, from which I extract the text and send it back to the user using `jsonify`.

On the client side, images are submitted, and the predicted text is retrieved using AJAX `fetch` and asynchronous operations with `async/await`. The server sends back a JSON file containing the predicted text or, if an error occurs, an error message. Feedback is then shown to the user using JavaScript to display the message.

I chose to use AJAX because it allows me to update only the desired elements without reloading the entire page, making the application more enjoyable to use.

Once the server receives the image, it checks if it is valid by verifying the file format. **Currently, only `png`, `jpg`, and `jpeg` are supported.** The file's content is verified using Pillow's `verify` function to ensure the integrity of the image.

I added a file size limitation of 16 MB to prevent large files from affecting performance and to prevent denial-of-service (DoS) attacks.

After checking for errors, I send the image to the appropriate model chosen by the user. Then, I save the predicted text in a database `ocr-results.db` with the date, time, and `user_id`.

Users can copy the predicted text for up to two hours using the table history. After expiration, the data is removed from the database using a scheduler that runs every hour. This process cleans up expired data and prevents storing data for too long.

I use cookies to identify users and show them the predicted text alongside the date and time they used the application for optical character recognition. Cookies are generated using a random universally unique identifier (UUID) with the function `uuid.uuid4()`. They are then stored on the client side and have a lifetime of two days before being regenerated.

Users can delete cookies and all stored data at any time by clicking the red button in the footer section.

### Files in the Repository

- **`API-and-config`**: This directory contains the `ocr_env.yaml` file and my OCR Space API key.
- **`CS50-video-project`**: This directory contains my video notes and some files used to make the video.
- **`database`**: This directory contains the SQLite3 database.
- **`static`**: This directory contains all images, videos, stylesheets, and JavaScript files.
- **`templates`**: This directory contains `index.html`. I have condensed my project into a single HTML page.
- **`test-images`**: This directory contains some images to test my model.
- **`.gitignore`**: This file is used to exclude unwanted files from commits.
- **`app.py`**: This file is my Flask server.
- **`requirements.txt`**: This file lists all the requirements necessary for the application to run.

Below is a guide on how to configure your environment using Miniconda or Python. I recommend using pip with Miniconda as it's the fastest.

#### Configure

The `ocr_env.yaml` file contains a list of all packages and dependencies.

> Note: The environment has only been tested on Windows machines.

To recreate the Conda environment named `ocr`:

1. Install Miniconda using the [Miniconda installer](https://docs.anaconda.com/miniconda/).
2. Open the Miniconda Command Line.
3. Navigate to the directory containing the `ocr_env.yaml` file.
4. Create the environment from the YAML file:

   ```sh
   conda env create -f ocr_env.yaml
   ```

---

You can also use pip to install the necessary packages:

1. **Ensure you have Python 3.11**: You can use the [Miniconda installer](https://docs.anaconda.com/miniconda/) to create a virtual environment with the following command or simply install Python 3.11 directly:

   ```bash
   conda create -n ocr python=3.11
   ```

2. **Install dependencies**: Activate your environment and run the following command to install the required packages:

   ```bash
   pip install tensorflow==2.12.0 keras-ocr seaborn jupyter opencv-python requests asyncio flask[async] Flask-Session httpx[http2] APScheduler cs50
   ```

---

**Note**:
- This README was text-corrected using GPT-4.
- The logo you see when viewing my `index.html` page was generated with DALL·E3.