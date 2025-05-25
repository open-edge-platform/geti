FROM python:3.10-slim-bookworm@sha256:49454d2bf78a48f217eb25ecbcb4b5face313fea6a6e82706465a6990303ada2 AS base

FROM base AS build

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter
# across both images.
ENV UV_PYTHON_DOWNLOADS=0

# Install the build dependencies for ldap
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev

# Copy the service dependencies
COPY --link --from=libs . libs

WORKDIR /platform/services/platform_cleaner

COPY --link --from=ghcr.io/astral-sh/uv:0.6.12@sha256:515b886e8eb99bcf9278776d8ea41eb4553a794195ef5803aa7ca6258653100d /uv /bin/uv

COPY --link app .

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-editable

FROM base AS runtime

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -l -u 10001 non-root && \
	pip3 uninstall -y setuptools pip wheel && \
    rm -rf /root/.cache/pip 

USER non-root

# Copy the application from the builder
COPY --link --from=build --chown=10001 /platform/services/platform_cleaner /platform/services/platform_cleaner

# Place executables in the environment at the front of the path
ENV PATH="/platform/services/platform_cleaner/.venv/bin:$PATH"
ENV PYTHONPATH="/platform/services/platform_cleaner"

WORKDIR /platform/services/platform_cleaner
