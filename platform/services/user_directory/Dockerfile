# replaced slim image to have gcc available
FROM ghcr.io/astral-sh/uv:python3.10-bookworm AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter
# across both images.
ENV UV_PYTHON_DOWNLOADS=0

# need to install the system dependencies for the python-ldap
RUN apt update && apt install -y libldap2-dev libsasl2-dev

# Copy the service dependencies
WORKDIR /builder
COPY --link --from=libs . libs
COPY --link --from=platform_libs . platform/libs
COPY --link --from=grpc_interfaces . grpc_interfaces

WORKDIR /builder/platform/services/user_directory

COPY --link app .

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv venv --relocatable && \
    uv sync --frozen --no-dev --no-editable

FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim

# need to install the system dependencies for the python-ldaplibraries
RUN apt update && apt install -y libldap2-dev && apt clean all && rm -rf /var/cache/apt/*

RUN useradd -l -u 10001 non-root
USER non-root

# Copy the application from the builder
COPY --link --from=builder --chown=10001 /builder/platform/services/user_directory /app
COPY --link entrypoint.sh /app
COPY --link logconfig.ini /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app
ENTRYPOINT [ "./entrypoint.sh" ]
