FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter across both images.
ENV UV_PYTHON_DOWNLOADS=0

# Copy the service dependencies
WORKDIR /builder
COPY --link --from=libs . libs
COPY --link --from=sc_sdk . interactive_ai/libs/sc_sdk
COPY --link --from=media_utils . interactive_ai/libs/media_utils

WORKDIR /builder/interactive_ai/services/visual_prompt

ADD app/ .

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv venv --relocatable && \
    uv sync --frozen --no-dev --no-editable

FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg=7:5.1.6-0+deb12u1 && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -l -u 10001 non-root

# Copy the application from the builder
COPY --link --from=builder --chown=10001 /builder/interactive_ai/services/visual_prompt /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

USER non-root
WORKDIR /app/services
CMD ["python", "main.py"]
