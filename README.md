# Web OCR Application

#### Video Demo: [video](URL-to-add)
TODO
#### Description:
My porject is a web application to performe Optical Character Recognition using deferent model.
It provie a ui to give a images prosses the images in the servver side and return the text predicted.
you can shose two deferent way to perfrome OCR for now only in English.
1. Using TensorFlow with ``keras_ocr`` where the model is run on the sever.
    - As of now I only use pre-trained model so the accuracy is okay in most cases. It still need more training and fine-tuning to get better results it's on my to-do list.
2. Using a OCR Space API that ise a cloud-based OCR servise that prosesse the image and return a the text with a very good accuracy.
I use cookies to indentifly user and show them what predicted text they have. They can copy the predicted text for two day after that the user cookie is change and the data is remove from the database using a sheduler cleaning that run every 1 hours. This is done to clean the expired data and to not keep data for two long.



#### Configure
The `ocr_env.yaml` file contains a list of all packages and dependencies.

>Note: Environment only tested on Windows machine.

To recreate the Conda environment named ``tf``:

1. Install Miniconda using the [Miniconda installer](https://docs.anaconda.com/miniconda/).
2. Open the Miniconda Command Line.
3. Navigate to the directory containing the `ocr_env.yaml` file.
4. Create the environment from the YAML file:
    ```sh
    conda env create -f ocr_env.yaml
    ```