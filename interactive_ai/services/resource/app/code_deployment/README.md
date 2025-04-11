# Code deployment
## Table of contents
- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Installation](#Installation)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Package contents](#package-contents)


## Introduction

This code deployment .zip archive contains:

1. Inference model(s) for your Intel® Geti™ project.

2. A sample image or video frame, exported from your project.   

3. A very simple code example to get and visualize the result of inference for your 
   project, on the sample image.
   
4. Jupyter notebooks with instructions and code for running inference locally for your project.

The deployment holds one model for each task in your project, so if for example 
you created a deployment for a `Detection -> Classification` project, it will consist of
both a detection, and a classification model. The Intel® Geti™ SDK is used to run 
inference for all models in the project's task chain.

This README describes the steps required to get the code sample up and running on your 
machine.

## Prerequisites

- [Python](https://www.python.org/downloads/) (>=3.9, <=3.12)

## Installation

1. Install [prerequisites](#prerequisites). You may also need to 
   [install pip](https://pip.pypa.io/en/stable/installation/). For example, on Ubuntu 
   execute the following command to install Python and pip:

   ```
   sudo apt install python3-dev python3-pip
   ```
   If you already have installed pip before, make sure it is up to date by doing:

   ```
   pip install --upgrade pip
   ```

2. Create a clean virtual environment: <a name="virtual-env-creation"></a>

   One of the possible ways for creating a virtual environment is to use `virtualenv`:

   ```
   python -m pip install virtualenv
   python -m virtualenv <directory_for_environment>
   ```

   Before starting to work inside the virtual environment, it should be activated:

   On Linux and macOS:

   ```
   source <directory_for_environment>/bin/activate
   ```

   On Windows:

   ```
   .\<directory_for_environment>\Scripts\activate
   ```

   Please make sure that the environment contains 
   [wheel](https://pypi.org/project/wheel/) by calling the following command:

   ```
   python -m pip install wheel
   ```

   > **NOTE**: On Linux and macOS, you may need to type `python3` instead of `python`.

3. In your terminal, navigate to the `example_code` directory in the code deployment 
   package.

4. Install requirements in the environment:

   ```
   python -m pip install -r requirements.txt
   ```

5. (Optional) Install the requirements for running the `demo_notebook.ipynb` Juypter notebook:

   ```
   python -m pip install -r requirements-notebook.txt
   ```
   
## Usage
### Local inference
Both `demo.py` script and the `demo_notebook.ipynb` notebook contain a code sample for:

1. Loading the code deployment (and the models it contains) into memory.

2. Loading the `sample_image.jpg`, which is a random image taken from the project you 
   deployed. 

3. Running inference on the sample image.

4. Visualizing the inference results.

### Inference with OpenVINO Model Server
Inference with OpenVINO Model Server (OVMS) is deprecated in Intel® Geti™ SDK.

To use OVMS, create a new model deployment in Intel® Geti™ and select "OpenVINO Model Server deployment". 
After downloading the deployment package, follow the included README instructions to run OVMS.

### Running the demo script

In your terminal:

1. Make sure the virtual environment created [above](#virtual-env-creation) is activated.

2. Make sure you are in the `example_code` directory in your terminal.

3. Run the demo using:
  
   ```
   python demo.py
   ```

The script will run inference on the `sample_image.jpg`. A window will pop up that 
displays the image, and the results of the inference visualized on top of it.

### Running the demo notebooks

In your terminal:

1. Make sure the virtual environment created [above](#virtual-env-creation) is activated.

2. Make sure you are in the `example_code` directory in your terminal.

3. Start JupyterLab using:
   
   ```
   jupyter lab
   ```
   
4. This should launch your web browser and take you to the main page of JupyterLab.

Inside JuypterLab:

5. In the sidebar of the JupyterLab interface, double-click on `demo_notebook.ipynb` open one of the notebooks.
   
6. Execute the notebook cell by cell to view the inference results. 


> **NOTE** The `demo_notebook.ipynb` is a great way to explore the `AnnotationScene` 
> object that is returned by the inference. The demo code only has very basic 
> visualization functionality, which may not be sufficient for all use case. For 
> example if your project contains many labels, it may not be able to visualize the 
> results very well. In that case, you should build your own visualization logic 
> based on the `AnnotationScene` returned by the `deployment.infer()` method.

## Troubleshooting

1. If you have access to the Internet through a proxy server only, please use pip 
   with a proxy call as demonstrated by the command below:

   ```
   python -m pip install --proxy http://<usr_name>:<password>@<proxyserver_name>:<port#> <pkg_name>
   ```

2. If you use Anaconda as environment manager, please consider that OpenVINO has 
   limited [Conda support](https://docs.openvino.ai/2021.4/openvino_docs_install_guides_installing_openvino_conda.html). 
   It is still possible to use `conda` to create and activate your python environment, 
   but in that case please use only `pip` (rather than `conda`) as a package manager 
   for installing packages in your environment.

3. If you have problems when you try to use the `pip install` command, please update 
   pip version as per the following command:
   ```
   python -m pip install --upgrade pip
   ```

## Package contents

The code deployment files are structured as follows:

- deployment
    - `project.json`
    - "<title of task 1>"  
        - model
          - `model.xml`
          - `model.bin`
          - `config.json`
        - python
          - model_wrappers
            - `__init__.py`
            - model_wrappers required to run demo
          - `README.md`
          - `LICENSE`
          - `demo.py`
          - `requirements.txt`
    - "<title of task 2>" (Optional)
        - ...
- example_code
    - `demo.py`
    - `demo_notebook.ipynb`
    - `demo_ovms.ipynb`  
    - `README.md`
    - `requirements.txt`
    - `requirements-notebook.txt`
- `sample_image.jpg`
- `LICENSE`