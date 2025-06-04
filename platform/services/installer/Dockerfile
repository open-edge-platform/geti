FROM ubuntu:20.04 AS base

RUN apt-get update -y && apt install software-properties-common -y && add-apt-repository ppa:deadsnakes/ppa -y
RUN apt-get install --no-install-recommends -y binutils curl python3.10 python3.10-dev python3.10-distutils
RUN rm /usr/bin/python3 && ln -s python3.10 /usr/bin/python3
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

FROM base AS build

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter
# across both images.
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /builder/installer/app

COPY --link --from=ghcr.io/astral-sh/uv:0.6.12 /uv /bin/uv

COPY --link app .
COPY --link --from=geti_controller_chart . geti_controller_chart
COPY --link --from=libs . libs

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv venv --relocatable && \
    uv sync --frozen --no-dev --no-editable

FROM base AS runtime

RUN useradd -l -u 10001 non-root && \
	pip3 uninstall -y setuptools pip wheel && \
    rm -rf /root/.cache/pip

USER non-root

# Copy the application from the builder
COPY --link --from=build --chown=10001 /builder/installer/app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# TODO remove templates when installation is handled by the GetiController
RUN pyinstaller \
    --exclude-module readline \
    --add-data "geti_controller_chart:geti_controller_chart" \
    --add-data "templates:templates" \
    --add-data "version.yaml:." \
    --add-data "system-packages.yaml:." \
    -F platform_installer.py
