# Geti GRPC interfaces

The `grpc_interfaces` module centralizes the definitions of gRPC interfaces for various components. Its primary goals are:
- **Avoid Code Duplication**: Provides a single source of truth for gRPC interface definitions, making them easier to maintain and ensuring consistency across components.
- **Multi-Language Support**: Enables seamless integration with both Python and Go by generating language-specific code from `.proto` files.

## Features
- Centralized `.proto` files for all gRPC interfaces.
- Support for multiple languages (Python, Go) with generated code.
- Easy-to-use `Makefile` for compiling `.proto` files and managing dependencies.
- Modular structure for adding, modifying, or using interfaces.

## Usage
Run the following command to see all available Makefile targets:

```bash
make help
```

## Directory Structure

```plaintext
grpc_interfaces/
├── credit_system/              # Module for the Credit System service
│   ├── service.proto           # .proto file defining the Credit System service
│   ├── pb/                     # Generated Python Protobuf definitions
|   ├── client.py               # Python client for the new service
│   └── go/                     # Go code
│       └── pb/                 # Generated Go Protobuf definitions
├── new_service/                # Example module for a new service
│   ├── service.proto           # .proto file defining the new service
│   ├── pb/                     # Generated Python Protobuf definitions
|   ├── client.py               # Python client for the new service
│   └── go/                     # Go code
│       └── pb/                 # Generated Go Protobuf definitions
├── tests/
│   └── unit/                   # Unit tests
│       ├── credit_system/      # Unit tests for Credit System service
|       └── new_service/        # Unit tests for the new service
├── Makefile                    # Build automation for generating code and managing dependencies
└── README.md                   # Documentation for the grpc_interfaces module
```

### Key Points:
- Each service (e.g., `credit_system`, `model_mesh`) has its own directory.
- The `.proto` file for the service resides in the module directory.
- Generated code for Python lives on the service's root directory.
- Generated code for Go lives under `go/` subdirectory.
- Python-specific unit tests are stored in the `tests/` directory under the corresponding service name.


## Instructions

### Use an existing interface

**Python**
1. Add required Python package with optional dependencies in client service `pyproject.toml`:

```toml
[project]
dependencies = [
    "grpc_interfaces[credit_system]"
]

[tool.uv.sources]
grpc_interfaces = { path="../grpc_interfaces" }
```

2. Import the generated Protobuf files and clients:

```python
from grpc_interfaces.credit_system.python.pb import credit_system_pb2, credit_system_pb2_grpc
from grpc_interfaces.credit_system.python import CreditSystemClient
```

**Go**
1. Add the `grpc_interfaces/go` module to your service:

```bash
go mod edit -replace geti.com/model_mesh=<GETI_CORE_HOME>/grpc_interfaces/model_mesh/go
go mod tidy
```

2. Import the generated Protobuf files and clients:

```go
import (
    "google.golang.org/grpc"

    clients "geti.com/grpc_api/clients"
    pb "geti.com/model_mesh/pb"    
)
```

### Create a new interface

1. Create a new .proto file in the appropriate directory under protos/. For example:

```
protos/new_service/new_service.proto
```

2. Generate the Protobuf files using the Makefile:

```bash
make generate-go-new_service # Generates only Go pb definitions for new_service
make generate-python-new_service # Generates only Python pb definitions for new_service
make generate-service-new_service # Generates both Python & Go pb definitions for new_service
```

### Modify an existing interface

> [!WARNING]  
> A gRPC interface is a contract between two or more components. Before committing any breaking change,
> determine what components depend on this interface and will be impacted, to minimize the risk of regression.

1. Update the .proto file in the protos/ directory.
2. Recompile the Protobuf files by running the corresponding Makefile target:

```bash
make generate-go-<service_name>
make generate-python-<service_name>
```

3. Update any Go/Python utilities or clients that depend on the modified interface.
