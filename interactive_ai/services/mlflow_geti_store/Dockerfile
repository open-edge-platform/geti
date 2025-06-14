FROM python:3.10-slim-bookworm@sha256:99d6b199420e2a3588649813218bef3e727fac9642d5da66c1c24ec96f7ec87d AS base

FROM base AS build

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter across both images.
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /interactive_ai/services/mlflow_geti_store

COPY --link --from=ghcr.io/astral-sh/uv:0.6.12@sha256:515b886e8eb99bcf9278776d8ea41eb4553a794195ef5803aa7ca6258653100d /uv /bin/uv

COPY --link mlflow_geti_store/ .
COPY --link entrypoints/ /entrypoints

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-editable


FROM base AS runtime

RUN useradd -l -u 10001 non-root && \
	pip3 uninstall -y setuptools pip wheel && \
    rm -rf /root/.cache/pip

COPY --link --from=build --chown=10001 /interactive_ai/services/mlflow_geti_store /interactive_ai/services/mlflow_geti_store

ARG VENV="/interactive_ai/services/mlflow_geti_store/.venv"
ENV PATH="$VENV/bin:$PATH"
ENV PYTHONPATH="/interactive_ai/services"

USER non-root
WORKDIR /interactive_ai/services/mlflow_geti_store
COPY --link --from=build --chown=10001 entrypoints/. .

COPY --chown=10001 --chmod=500 /entrypoints/check_liveliness ${VENV}/bin/
COPY --chown=10001 --chmod=500 /entrypoints/run_with_liveliness_checking ${VENV}/bin/
COPY --chown=10001 --chmod=500 /entrypoints/run ${VENV}/bin/

ENTRYPOINT ["sh", "run_with_liveliness_checking"]
