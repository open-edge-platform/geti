FROM python:3.10-slim-bookworm AS base

FROM base AS build

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter
# across both images.
ENV UV_PYTHON_DOWNLOADS=0

# Copy the service dependencies
WORKDIR /builder
COPY --link --from=libs . ../libs

WORKDIR /builder/credit_system/app

COPY --link --from=ghcr.io/astral-sh/uv:0.6.12 /uv /bin/uv

COPY --link app .

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
COPY --link --from=build --chown=10001 /builder/credit_system/app /app
COPY --link entrypoint.sh /app
COPY --link logconfig.ini /app
COPY --link migration.sh /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app
ENTRYPOINT [ "./entrypoint.sh" ]
