FROM python:3.10-slim-bookworm@sha256:99d6b199420e2a3588649813218bef3e727fac9642d5da66c1c24ec96f7ec87d AS base

FROM base AS build

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter
# across both images.
ENV UV_PYTHON_DOWNLOADS=0

# Copy the service dependencies
COPY --link --from=libs . libs

WORKDIR /platform/services/onboarding_service

COPY --link --from=ghcr.io/astral-sh/uv:0.6.12@sha256:515b886e8eb99bcf9278776d8ea41eb4553a794195ef5803aa7ca6258653100d /uv /bin/uv

COPY --link app .

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-editable

FROM base AS runtime

RUN useradd -l -u 10001 non-root && \
	pip3 uninstall -y setuptools pip wheel && \
    rm -rf /root/.cache/pip

USER non-root

# Copy the application from the builder
COPY --link --from=build --chown=10001 /platform/services/onboarding_service /platform/services/onboarding_service
COPY --link entrypoint.sh /platform/services/onboarding_service
COPY --link logconfig.ini /platform/services/onboarding_service

# Place executables in the environment at the front of the path
ENV PATH="/platform/services/onboarding_service/.venv/bin:$PATH"

WORKDIR /platform/services/onboarding_service
ENTRYPOINT [ "./entrypoint.sh" ]
