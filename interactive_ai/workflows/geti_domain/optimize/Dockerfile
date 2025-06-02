FROM python:3.10-slim-bookworm@sha256:49454d2bf78a48f217eb25ecbcb4b5face313fea6a6e82706465a6990303ada2 AS base

FROM base AS build

# Install Git and clone the OTX at the specified tag
ARG OTX_RELEASE_TAG=2.4.2

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git
RUN git clone --branch $OTX_RELEASE_TAG --single-branch https://github.com/open-edge-platform/training_extensions.git

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter across both images.
ENV UV_PYTHON_DOWNLOADS=0

# Copy the service dependencies
COPY --link --from=common . interactive_ai/workflows/geti_domain/common
COPY --link --from=libs . libs
COPY --link --from=iai_core . interactive_ai/libs/iai_core_py
COPY --link --from=media_utils . interactive_ai/libs/media_utils

WORKDIR /interactive_ai/workflows/geti_domain/workflow

COPY --link --from=ghcr.io/astral-sh/uv:0.6.12@sha256:515b886e8eb99bcf9278776d8ea41eb4553a794195ef5803aa7ca6258653100d /uv /bin/uv

COPY --link job/ job

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-editable

FROM base AS runtime

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1=1.6.* \
    libglib2.0-0=2.74.* \
    curl && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -l -u 10001 non-root && \
	pip3 uninstall -y setuptools pip wheel && \
    rm -rf /root/.cache/pip

# Copy the application from the builder
COPY --link --from=build --chown=10001 /interactive_ai/workflows/geti_domain/workflow /interactive_ai/workflows/geti_domain/workflow
COPY --link --from=build --chown=10001 /training_extensions/src/otx/tools/templates /model_templates

ENV MODEL_TEMPLATES_DIR=/model_templates

# Place executables in the environment at the front of the path
ENV PATH="/interactive_ai/workflows/geti_domain/workflow/.venv/bin:$PATH"
ENV PYTHONPATH="/interactive_ai/workflows/geti_domain/workflow"

USER non-root
WORKDIR /interactive_ai/workflows/geti_domain/workflow
