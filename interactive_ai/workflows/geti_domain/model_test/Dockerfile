FROM python:3.10-slim-bookworm AS base

FROM base AS build

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter across both images.
ENV UV_PYTHON_DOWNLOADS=0

# Copy the service dependencies
WORKDIR /builder
COPY --link --from=common . interactive_ai/workflows/geti_domain/common
COPY --link --from=libs . libs
COPY --link --from=iai_core . interactive_ai/libs/iai_core_py
COPY --link --from=media_utils . interactive_ai/libs/media_utils
COPY --link --from=grpc_interfaces . grpc_interfaces

WORKDIR /builder/interactive_ai/workflows/geti_domain/workflow

COPY --link --from=ghcr.io/astral-sh/uv:0.6.12 /uv /bin/uv

COPY --link job/ job

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-editable

FROM base AS runtime

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1=1.6.0-1 \
    libglib2.0-0=2.74.6-2+deb12u5 \
    curl && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -l -u 10001 non-root && \
	pip3 uninstall -y setuptools pip wheel && \
    rm -rf /root/.cache/pip

# Copy the application from the builder
COPY --link --from=build --chown=10001 /builder/interactive_ai/workflows/geti_domain/workflow /builder/interactive_ai/workflows/geti_domain/workflow

# Place executables in the environment at the front of the path
ENV PATH="/builder/interactive_ai/workflows/geti_domain/workflow/.venv/bin:$PATH"
ENV PYTHONPATH="/builder/interactive_ai/workflows/geti_domain/workflow"

USER non-root
WORKDIR /builder/interactive_ai/workflows/geti_domain/workflow
