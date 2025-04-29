# GRPC Predict V2 Protocol

The grpc_predict_v2.proto file defines the gRPC interface for inference services. It is based on the [Kubeflow Inference Protocol](https://github.com/kserve/kserve/blob/master/docs/predict-api/v2/README.md) and provides a standardized way to interact with inference servers. This protocol is designed to support various inference-related operations, such as checking server readiness, retrieving metadata, and performing model inference.

## Features
The protocol includes the following key features:

- **Server Status APIs**:
    - `ServerLive`: Check if the server is live.
    - `ServerReady`: Check if the server is ready for inference.
    - `ServerMetadata`: Retrieve metadata about the server.
- **Model Status APIs**:
    - `ModelReady`: Check if a specific model is ready for inference.
    - `ModelMetadata`: Retrieve metadata about a specific model.
- **Inference API**:
    - `ModelInfer`: Perform inference using a specific model.

## Dependencies
The [grpc_predict_v2.proto](./grpc_predict_v2.proto) file imports the `google/api/annotations.proto` file to define HTTP bindings for the gRPC methods. This allows the gRPC services to be exposed as RESTful APIs using gRPC-HTTP transcoding.

### Required Dependencies

- **Google API Common Protos**:
    - The `google/api/annotations.proto` file is part of the [Google API Common Protos](https://github.com/googleapis/googleapis). Ensure that these protos are available in your environment when compiling the .proto file.

#### Install Dependences

To download the required `.proto` files, run the following commands:

```bash
sudo mkdir -p ./google/api

sudo curl -L https://raw.githubusercontent.com/googleapis/googleapis/master/google/api/annotations.proto -o ./google/api/annotations.proto
sudo curl -L https://raw.githubusercontent.com/googleapis/googleapis/master/google/api/http.proto -o ./google/api/http.proto
```
