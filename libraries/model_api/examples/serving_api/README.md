# Serving API example

This example demonstrates how to use a Python API of OpenVINO Model API for a remote inference of models hosted with [OpenVINO Model Server](https://docs.openvino.ai/2026/model-server/ovms_what_is_openvino_model_server.html). This tutorial assumes that you are familiar with Docker subsystem and includes the following steps:

- Run Docker image with
- Instantiate a model
- Run inference
- Process results

## Prerequisites

- Install Model API from source with `ovms` dependencies by running

- ```bash
  uv sync --extra examples
  ```

- Install Docker. Please refer to the [official documentation](https://docs.docker.com/get-docker/) for details.

- Download sample models and images by running `uv run python tests/accuracy/download_models.py -d data -j tests/accuracy/examples.json -l` and resave a configured model at OVMS friendly folder layout:

  ```bash
  mkdir -p data/ovms/ssd-card-detection/1
  cp data/otx_models/ssd-card-detection.* data/ovms/ssd-card-detection/1/
  ```

- Run docker with OVMS server:

  ```bash
  docker run -d -v $(/bin/pwd)/data/ovms:/models -p 8000:8000 openvino/model_server:latest --model_path /models/ssd-card-detection --model_name ssd-card-detection --rest_port 8000 --nireq 4 --target_device CPU
  ```

## Run example

To run the example, please execute the following command:

```bash
uv run python examples/serving_api/run.py data/cards.png
```
