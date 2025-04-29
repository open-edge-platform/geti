FROM python:3.10-slim-bookworm AS base

FROM base AS build

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter
# across both images.
ENV UV_PYTHON_DOWNLOADS=0

# need to install the system dependencies for the python-ldap
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev

# Copy the service dependencies
WORKDIR /builder
COPY --link --from=common_libs . libs
COPY --link --from=platform_libs . platform/libs
COPY --link --from=grpc_interfaces . grpc_interfaces

WORKDIR /builder/platform/services/initial_user

COPY --link --from=ghcr.io/astral-sh/uv:0.6.12 /uv /bin/uv

COPY --link app .

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv venv --relocatable && \
    uv sync --frozen --no-dev --no-editable

FROM base AS runtime

# need to install the system dependencies for the python-ldap libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libsasl2-2 \
    libldap-2.5-0 && \
    apt clean all && \
    rm -rf /var/cache/apt/* && \
    useradd -l -u 10001 non-root && \
	pip3 uninstall -y setuptools pip wheel && \
    rm -rf /root/.cache/pip

USER non-root

# Copy the application from the builder
COPY --link --from=build --chown=10001 /builder/platform/services/initial_user /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app
