FROM python:3.10-slim-bookworm@sha256:49454d2bf78a48f217eb25ecbcb4b5face313fea6a6e82706465a6990303ada2 AS base

FROM base AS build

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter across both images.
ENV UV_PYTHON_DOWNLOADS=0

# Copy the service dependencies
COPY --link --from=libs . libs
COPY --link --from=data_migration . interactive_ai/data_migration

WORKDIR /interactive_ai/migration_job

COPY --link --from=ghcr.io/astral-sh/uv:0.6.12@sha256:515b886e8eb99bcf9278776d8ea41eb4553a794195ef5803aa7ca6258653100d /uv /bin/uv

COPY --link migration_job/ .

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-editable

FROM base AS runtime

# Install ffmpeg and curl
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg=7:5.1.6-0+deb12u1 curl && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -l -u 10001 non-root && \
	pip3 uninstall -y setuptools pip wheel && \
    rm -rf /root/.cache/pip

COPY --link --from=build --chown=10001 /interactive_ai/migration_job /interactive_ai/migration_job

ARG VENV="/interactive_ai/migration_job/.venv"
ENV PATH="$VENV/bin:$PATH"
ENV PYTHONPATH="/interactive_ai"

USER non-root
WORKDIR /interactive_ai/migration_job
COPY --link --chown=10001 entrypoint.sh /interactive_ai/migration_job
ENTRYPOINT [ "./entrypoint.sh"]
