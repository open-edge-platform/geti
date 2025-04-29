# Contributing to Intel® Geti™

## Welcome! 🌟

Thank you for your interest in contributing to Intel® Geti™. This guide will help you understand our project structure,
development workflow, and contribution guidelines.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Security](#security)
- [How to Contribute](#how-to-contribute)
- [Development Guidelines](#development-guidelines)
- [Sign your work](#sign-your-work)
- [License](#license)

## Code of Conduct

This project and everyone participating in it are governed by the [`CODE_OF_CONDUCT`](CODE_OF_CONDUCT.md) document. By
participating, you are expected to adhere to this code.

## Security

Read the [`Security Policy`](SECURITY.md).

## How to Contribute

### Contribute Code Changes

If you'd like to help improve Intel® Geti™, pick one of the issues listed in [GitHub
Issues](https://github.com/open-edge-platform/geti/issues) and submit
a [Pull Request](https://github.com/open-edge-platform/geti/pulls) to address it.
Note: Before you start working on it, please make sure the change hasn’t already been implemented.

### Report Bugs

If you encounter a bug, please open an issue in [`Github Issues`](https://github.com/open-edge-platform/geti/issues).
Be sure to include all the information requested in the bug report template to help us understand and resolve the issue
quickly.

### Suggest Enhancements

Intel welcomes suggestions for new features and improvements. Follow these steps to make a suggestion:

- Check if there's already a similar suggestion in [`Github Issues`](https://github.com/open-edge-platform/geti/issues).
- If not, please open a new issue and provide the information requested in the feature request template.

### Submit Pull Requests

Before submitting a pull request, ensure you follow these guidelines:

- Fork the repository and create your branch from `main`.
- Follow the [`Development Guidelines`](#development-guidelines) in this document.
- Test your changes thoroughly.
- Document your changes (in code, readme, etc.).
- Submit your pull request, detailing the changes and linking to any relevant issues.
- Wait for a review. Intel will review your pull request as soon as possible and provide you with feedback.
  You can expect a merge once your changes are validated with automatic tests and approved by maintainers.

## Development Guidelines

### Project Overview

Intel® Geti™ project is a monorepo designed to support independent development and release of multiple related
subprojects while maintaining a cohesive platform. Our architecture allows for flexible and modular development across
different components.

### Repository Structure

#### Directory Layout

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

#### Component Structure

Each component typically includes:

- `app/`: Source code
- `chart/`: Helm chart for Kubernetes deployment
- `Dockerfile`: Container build specifications
- `makefile`: Component-specific build targets
- `version`: Component version tracking file

#### Library Types

1. **Group-Specific Libraries**
    - Scoped to specific service groups
    - Minimize rebuild dependencies
    - Prevent unnecessary cross-component coupling

2. **Cross-Project Libraries**
    - Shared across entire monorepo
    - Kept minimal to reduce rebuild impact
    - Contains universal utilities and shared resources

### Getting Started

#### Prerequisites

Before you begin, ensure you have:

- Local Kubernetes cluster (kind, k3s, or minikube)
- Docker
- Helm (v3+)
- kubectl
- make (optional)

#### Setup Steps

1. Clone the repository
2. Set up your local Kubernetes environment (TBD)
3. Configure local Docker registry (TBD)

### Local Development

#### Building a project or component

```bash
# Navigate to the component directory
cd path/to/component

# Build the component
make build-image

# Run tests
make tests
```

#### Build Targets

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

### Deployment

#### Full Platform Deployment

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

#### Individual Component Deployment

```bash
# Build and push a specific component to your local registry
make -C subproject-name build-image push-image REGISTRY_URL=$REGISTRY_URL

# Repackage platform charts
make helm-package-dev REGISTRY_URL=$REGISTRY_URL

# Update running platform
helm upgrade --install geti ./platform-chart -f .dev.values.yaml
```

#### Working with the Umbrella Chart

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

## Sign your work

Please use the sign-off line at the end of the patch. Your signature certifies that you wrote the patch or otherwise
have the right to pass it on as an open-source patch. The rules are pretty simple: if you can certify
the below (from [developercertificate.org](http://developercertificate.org/)):

```
Developer Certificate of Origin
Version 1.1

Copyright (C) 2004, 2006 The Linux Foundation and its contributors.
660 York Street, Suite 102,
San Francisco, CA 94110 USA

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.

Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```

Then you just add a line to every git commit message:

    Signed-off-by: Joe Smith <joe.smith@email.com>

Use your real name (sorry, no pseudonyms or anonymous contributions.)

If you set your `user.name` and `user.email` git configs, you can sign your
commit automatically with `git commit -s`.

## License

Intel® Geti™ is licensed under the terms in [LICENSE](LICENSE). By contributing to the project, you agree
to the license and copyright terms therein and release your contribution under these terms.
