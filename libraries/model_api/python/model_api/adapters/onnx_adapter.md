# ONNX Runtime Adapter

The `ONNXRuntimeAdapter` implements `InferenceAdapter` interface. The `ONNXRuntimeAdapter` allows Model API to leverage ONNX Runtime for inference.

## Prerequisites

`ONNXRuntimeAdapter` enables inference via ONNX Runtime, and we need to install it first:

```sh
pip install onnx onnxruntime
```

### ONNX metadata

ModelAPI uses IR RTInfo to store metadata (wrapper-specific parameters, preprocessing parameters, labels list, etc.).
For details see the implementation of `Model._load_config()` method.
To embed that metadata into ONNX file, one can use ONNX properties: `metadata_props.add()` and use
ModelAPI-specific parameters as metadata keys with exactly the same names as in RTInfo, but split by spaces:
`"model_info model_type"` and so on.

## Limitations

- `ONNXRuntimeAdapter` is available in Python version of ModelAPI only.
- Although `ONNXRuntimeAdapter` doesn't use OpenVINO directly, OV should be installed, because Model API depends on it at
  the low level.
- Model reshape is not supported, and input shape should be defined in the model (excluding batch dimension) to perform
  shape inference and parse model outputs successfully.
- `model.load()` method does nothing, model is loaded in the constructor of `ONNXRuntimeAdapter`.
- `ONNXRuntimeAdapter` supports only python-based preprocessing, and sometimes it gives slightly different results, than
  OpenVINO operations graph-based preprocessing. Therefore, inference results can also be different than when using `OpenvinoAdapter`.
- Models scope is limited to `SSD`, `MaskRCNNModel`, `SegmentationModel`, and `ClassificationModel` wrappers.

## Running a model with ONNXRuntimeAdapter

The process of construction of a model with `ONNXRuntimeAdapter` is similar to one with `OpenvinoAdapter`, but
ONNX Runtime session parameters are forwarded to ORT instead of OpenVINO-specific parameters:

```python
import cv2
# import model wrapper class
from model_api.models import SSD
# import inference adapter
from model_api.adapters import ONNXRuntimeAdapter

# read input image using opencv
input_data = cv2.imread("sample.png")

# define the path to mobilenet-atss model in IR format
model_path = "data/otx_models/det_mobilenetv2_atss_bccd.onnx"

# create adapter for ONNX runtime, pass the model path
inference_adapter = ONNXRuntimeAdapter(model_path, ort_options={"providers" : ['CPUExecutionProvider']})

# create model API wrapper for SSD architecture
# preload=True is required for consistency
ssd_model = SSD(inference_adapter, preload=True)

# apply input preprocessing, sync inference, model output postprocessing
results = ssd_model(input_data)
```
