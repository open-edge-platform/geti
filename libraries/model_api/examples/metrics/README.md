# Benchmark - a metrics API example

This example demonstrates how to use the Python API of OpenVINO Model API for performance analysis and metrics collection during model inference. This tutorial includes the following features:

- Model performance measurement
- Configurable device selection (CPU, GPU, etc.)
- Automatic image dataset discovery
- Warm-up and test runs with customizable parameters
- Detailed inference time analysis
- Metrics logging and reporting
- Performance statistics calculation

## Prerequisites

Install Model API dependencies with examples by running the following command in the root directory of the repository:

```bash
uv sync --extra examples
```

## Run example

To run the example, please execute the following command:

```bash
python benchmark.py <model_path> <dataset_path> [options]
```

### Required Arguments

- `model_path` - Path to the model file (.xml)
- `dataset_path` - Path to the dataset directory containing test images

### Optional Arguments

- `--device` - Device to run the model on (default: CPU)
- `--warmup-runs` - Number of warmup runs (default: 5)
- `--test-runs` - Number of test runs (default: 100)

### Examples

```bash
# Basic usage with CPU
uv run python benchmark.py /path/to/model.xml /path/to/images

# Use GPU with custom parameters
uv run python benchmark.py /path/to/model.xml /path/to/images --device GPU --warmup-runs 10 --test-runs 50

# Show help
uv run python benchmark.py --help
```

### Example with pre-trained model

In the root directory of the repository:

- download sample models and images by running `uv run python tests/accuracy/download_models.py -d data -j tests/accuracy/examples.json -l`
- run the example with the following command: `uv run python examples/metrics/benchmark.py data/otx_models/ssd-card-detection.xml data/coco128/images/train2017`

## Expected Output

The example will display:

- Number of images found in the dataset directory
- Progress updates during warm-up and test phases
- Comprehensive performance analysis results including timing statistics
- Detailed metrics about the model's inference performance on the specified device

Example output

```bash
OpenVINO Runtime
   build: 2025.2.0-19140-c01cd93e24d-releases/2025/2
Reading model model.xml
The model model.xml is loaded to CPU
   Number of model infer requests: 2
Starting warm-up...
Running 100 test inferences...
  Completed 10/100
  Completed 20/100
  Completed 30/100
  Completed 40/100
  Completed 50/100
  Completed 60/100
  Completed 70/100
  Completed 80/100
  Completed 90/100
  Completed 100/100
============================================================
               🚀 PERFORMANCE METRICS REPORT 🚀
============================================================

📊 Model Loading:
   Load Time: 2.497s

⚙️  Processing Times (mean ± std):
   Preprocess:  0.001s ± 0.000s
   Inference:   0.570s ± 0.020s
   Postprocess: 0.001s ± 0.000s

📈 Total Time Statistics:
   Mean:  0.572s ± 0.020s
   Min:   0.556s
   Max:   0.642s

🎯 Performance Summary:
   Total Frames: 100
   FPS:          1.75
============================================================
```
