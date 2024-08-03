# Web OCR Application

#### Video Demo: [video](URL-to-add)
TODO
#### Description:
My project is a web application for performing Optical Character Recognition (OCR) using different models. It provides a user interface to upload images, processes the images on the server side, and returns the predicted text. You can choose between two different methods to perform OCR, __currently available only in English__:

1. **Using TensorFlow with `keras_ocr`**: The model runs on the server. Link to [keras-ocr documentation](https://keras-ocr.readthedocs.io/) and [GitHub repository](https://github.com/faustomorales/keras-ocr).
    - Currently, I am using a pre-trained model, which provides acceptable accuracy in most cases. It still requires additional training and fine-tuning to achieve better results, which is on my to-do list.

2. **Using the OCR Space API**: This is a cloud-based OCR service that processes the image and returns the text with very good accuracy using their OCR Engine 2. link to [OCR Space API](https://ocr.space/ocrapi).

I use cookies to identify users and show them the predicted text they have generated. Users can copy the predicted text for up to two days, after that, the user cookie is changed, and the data is removed from the database using a scheduler that runs every hour. This is done to clean up expired data and avoid keeping data for too long.

#### Configure
The `ocr_env.yaml` file contains a list of all packages and dependencies.

>Note: Environment only tested on Windows machines.

To recreate the Conda environment named ``ocr``:

1. Install Miniconda using the [Miniconda installer](https://docs.anaconda.com/miniconda/).
2. Open the Miniconda Command Line.
3. Navigate to the directory containing the `ocr_env.yaml` file.
4. Create the environment from the YAML file:
    ```sh
    conda env create -f ocr_env.yaml
    ```
---

You can also use pip to install the necessary packages:

1. **Ensure you have Python 3.11**: You can use the [Miniconda installer](https://docs.anaconda.com/miniconda/) and create a virtual environment with the following command or simply install Python 3.11 directly:

   ```bash
   conda create -n ocr python=3.11
   ```

2. **Install dependencies**: Activate your environment and run the following command to install the required packages:

   ```bash
   pip install tensorflow==2.12.0 keras-ocr seaborn jupyter opencv-python requests asyncio flask[async] Flask-Session httpx httpx[http2] APScheduler
   ```
---

**Note**: This README was corrected and styled using GPT-4.
