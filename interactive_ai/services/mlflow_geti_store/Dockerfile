FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter across both images.
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /builder/interactive_ai/services/mlflow_geti_store

ADD mlflow_geti_store/ .
ADD entrypoints/ /entrypoints

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv venv --relocatable && \
    uv sync --frozen --no-dev --no-editable


FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim AS mlflow_geti_store
# Copy the application from the builder
RUN useradd -l -u 10001 non-root

COPY --link --from=builder --chown=10001 /builder/interactive_ai/services/mlflow_geti_store /app/mlflow_geti_store

ARG VENV="/app/mlflow_geti_store/.venv"
ENV PATH="$VENV/bin:$PATH"
ENV PYTHONPATH="/app"

USER non-root
WORKDIR /app
COPY --link --from=builder --chown=10001 entrypoints/. .

COPY --chown=10001 --chmod=500 /entrypoints/check_liveliness ${VENV}/bin/
COPY --chown=10001 --chmod=500 /entrypoints/run_with_liveliness_checking ${VENV}/bin/
COPY --chown=10001 --chmod=500 /entrypoints/run ${VENV}/bin/

ENTRYPOINT ["sh", "run_with_liveliness_checking"]
