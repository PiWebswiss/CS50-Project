# Web OCR Application

#### Video Demo: [video](URL-to-add)
TODO
#### Description:
TODO

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