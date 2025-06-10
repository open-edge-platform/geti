FROM python:3.10-slim-bookworm@sha256:2ee0fb8794bf82af1b2db168ada5869b4c27d17720dd3b155b56c111fb4a38ae AS base

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

# Step 1: Install runtime dependencies and intel graphics libs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1=1.6.* \
    libglib2.0-0=2.74.* \
    software-properties-common \
    gpg \
    wget \
    curl && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -l -u 10001 non-root && \
    pip3 uninstall -y setuptools pip wheel && \
    rm -rf /root/.cache/pip

RUN wget -qO /tmp/intel-graphics.key https://repositories.intel.com/gpu/intel-graphics.key && \
    gpg --yes --dearmor --output /usr/share/keyrings/intel-graphics.gpg /tmp/intel-graphics.key
RUN echo "deb [arch=amd64,i386 signed-by=/usr/share/keyrings/intel-graphics.gpg] https://repositories.intel.com/gpu/ubuntu jammy unified" | tee /etc/apt/sources.list.d/intel-gpu-jammy.list
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libze-intel-gpu1 libze1 intel-opencl-icd clinfo libze-dev intel-ocloc
# Remove unnecessary packages and files to reduce the final image size
RUN apt-get purge -y --auto-remove gpg wget && \
    rm -rf /root/.cache \
    /var/cache/apt/* /var/lib/apt/lists/* /var/log/* \
    /tmp/* \
    /usr/share/man/* /usr/share/doc/*

# step 2: get python dependencies
FROM base AS build

# Copy the service dependencies
COPY --link --from=libs . libs

WORKDIR /interactive_ai/workflows/otx_domain/trainer/otx_v2

COPY --link --from=ghcr.io/astral-sh/uv:0.6.12@sha256:515b886e8eb99bcf9278776d8ea41eb4553a794195ef5803aa7ca6258653100d /uv /bin/uv

COPY --link scripts/ scripts
COPY --link run run
COPY --link download_pretrained_weights.py download_pretrained_weights.py

# For OTX to install torch with ipex support, else defaults to cpu version
ENV PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/xpu

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-editable

# step 3: build final runtime image
FROM base AS runtime

# Copy the application from the builder
COPY --link --from=build --chown=10001 /interactive_ai/workflows/otx_domain/trainer/otx_v2 /interactive_ai/workflows/otx_domain/trainer/otx_v2

# Place executables in the environment at the front of the path
ENV PATH="/interactive_ai/workflows/otx_domain/trainer/otx_v2/.venv/bin:/interactive_ai/workflows/otx_domain/trainer/otx_v2:$PATH"
ENV PYTHONPATH="/interactive_ai/workflows/otx_domain/trainer/otx_v2"
ENV HF_HUB_OFFLINE=1

USER non-root
WORKDIR /home/non-root
WORKDIR /interactive_ai/workflows/otx_domain/trainer/otx_v2
