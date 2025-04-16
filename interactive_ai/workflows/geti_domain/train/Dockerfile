FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim AS builder

# Install Git and clone the OTX at the specified tag
ARG OTX_RELEASE_TAG=2.4.0

RUN apt-get update && apt-get install -y git
RUN git clone --branch $OTX_RELEASE_TAG --single-branch https://github.com/open-edge-platform/training_extensions.git

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter across both images.
ENV UV_PYTHON_DOWNLOADS=0

# Copy the service dependencies
WORKDIR /builder
COPY --link --from=common . interactive_ai/workflows/geti_domain/common
COPY --link --from=libs . libs
COPY --link --from=sc_sdk . interactive_ai/libs/sc_sdk
COPY --link --from=media_utils . interactive_ai/libs/media_utils
COPY --link --from=grpc_interfaces . grpc_interfaces

WORKDIR /builder/interactive_ai/workflows/geti_domain/workflow

ADD job/ job

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-editable

FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim
RUN useradd -l -u 10001 non-root

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1=1.6.0-1 \
    libglib2.0-0=2.74.6-2+deb12u5 \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Copy the application from the builder
COPY --link --from=builder --chown=10001 /builder/interactive_ai/workflows/geti_domain/workflow /builder/interactive_ai/workflows/geti_domain/workflow
COPY --link --from=builder --chown=10001 /training_extensions/src/otx/tools/templates /model_templates

ENV MODEL_TEMPLATES_DIR=/model_templates

# Place executables in the environment at the front of the path
ENV PATH="/builder/interactive_ai/workflows/geti_domain/workflow/.venv/bin:$PATH"
ENV PYTHONPATH="/builder/interactive_ai/workflows/geti_domain/workflow"

USER non-root
WORKDIR /builder/interactive_ai/workflows/geti_domain/workflow
