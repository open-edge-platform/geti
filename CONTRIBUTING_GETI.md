# Contributing to Geti

## Welcome! 🌟

Thank you for your interest in contributing to Geti. This guide will help you understand our project structure,
development workflow, and contribution guidelines.

## Table of Contents

- [Project Overview](#project-overview)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Local Development](#local-development)
- [Deployment](#deployment)
- [Contribution Process](#contribution-process)
- [Release Management](#release-management)

## Project Overview

Geti is a monorepo designed to support independent development and release of multiple related subprojects while
maintaining a cohesive platform. Our architecture allows for flexible and modular development across different
components.

## Repository Structure

### Directory Layout

```
├── Makefile.shared-*             # Shared build targets for different languages (go, js, python)
├── interactive_ai/               # Group of components
│   ├── services/                 # Group-specific libraries
│   ├── workflows/                # Nested group of components
│   ├── libs/                     # Nested group of components
│   └── makefile                  # Group-level build orchestration
├── libs/                         # Cross-project shared libraries
└── makefile                      # Project-level build orchestration
```

### Component Structure

Each component typically includes:

- `app/`: Source code
- `chart/`: Helm chart for Kubernetes deployment
- `Dockerfile`: Container build specifications
- `makefile`: Component-specific build targets
- `version`: Component version tracking file

### Library Types

1. **Group-Specific Libraries**
    - Scoped to specific service groups
    - Minimize rebuild dependencies
    - Prevent unnecessary cross-component coupling

2. **Cross-Project Libraries**
    - Shared across entire monorepo
    - Kept minimal to reduce rebuild impact
    - Contains universal utilities and shared resources

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- Local Kubernetes cluster (kind, k3s, or minikube)
- Docker
- Helm (v3+)
- kubectl
- make (optional)

### Setup Steps

1. Clone the repository
2. Set up your local Kubernetes environment (TBD)
3. Configure local Docker registry (TBD)

## Local Development

### Building a project or component

```bash
# Navigate to the component directory
cd path/to/component

# Build the component
make build-image

# Run tests
make tests
```

### Build Targets

- `clean`: Remove build artifacts
- `lint`: Run linter in "fix" mode to automatically correct code where possible
- `static-code-analysis`: Run static analysis/linters in read-only mode
- `test-unit`: Run unit tests
- `test-integration`: Run integration tests
- `test-component`: Run component-specific tests
- `test`: Run all types of tests
- `coverage`: Run tests and generate a coverage profile
- `build`: Create binaries
- `publish`: Publish artifacts to registries
- `build-image`: Build a container image
- `push-image`: Publish a container image
- `lint-chart`: Lint a helm chart
- `publish-chart`: Publish a helm chart

## Deployment

### Full Platform Deployment

```bash
# Build and push all component images to your local registry 
make build-image push-image REGISTRY_URL=$REGISTRY_URL

# Package platform charts. This target does the following:
# - Packages components Helm charts and the platform umbrella chart.
# - Generates a `.dev.values.yaml` file overriding the umbrella chart's dependencies to use local chart packages
#   with their latest versions, and pointing to the local registry.
make helm-package-dev REGISTRY_URL=$REGISTRY_URL

# Deploy platform
helm upgrade --install geti ./platform-chart -f .dev.values.yaml
```

### Individual Component Deployment

```bash
# Build and push a specific component to your local registry
make -C subproject-name build-image push-image REGISTRY_URL=$REGISTRY_URL

# Repackage platform charts
make helm-package-dev REGISTRY_URL=$REGISTRY_URL

# Update running platform
helm upgrade --install geti ./platform-chart -f .dev.values.yaml
```

### Working with the Umbrella Chart

The platform uses an umbrella Helm chart (located in the `platform-chart/` directory) to coordinate the deployment of
all subprojects:

1. **Modify the umbrella chart's dependencies configuration**:

   The `platform-chart/Chart.yaml` file contains dependency references:

   ```yaml
   dependencies:
     - name: account-service
       version: "^1.0.0"  # Allows any 1.x.x version
       repository: "file://../account-service/charts/account-service"
       condition: account-service.enabled
     - name: resource-ms
       version: "^2.0.0"  # Allows any 2.x.x version
       repository: "file://../iai/services/resource-ms/charts/resource-ms"
       condition: resource-ms.enabled
   ```

   For development, you can:
    - Change `version` fields to `*` to always use the latest version
    - Use `file://` repository references to local charts
    - Enable/disable components with conditions in `values-dev.yaml`

2. **Test specific component versions**:

   Create a custom values file that overrides specific chart versions:

   ```yaml
   # my-test-values.yaml
   account-service:
     chart:
       version: 1.2.3
   resource-ms:
     chart: 
       version: 2.3.4
   ```

   Then apply it:
   ```bash
   helm upgrade --install geti ./platform-chart \
     -f ./dev.values.yaml \
     -f ./my-test-values.yaml
   ```

## Release Management

### Component Releases

- Versions tracked in `version` file
- CI builds and publishes artifacts
- Tagged with component name and version

### Platform Releases

- Managed via umbrella Helm chart
- Independent versioning
- Represents validated component combinations

## Need Help?

- Review documentation
- Open a repository issue
- Contact project maintainers

**Happy Contributing!** 🚀
