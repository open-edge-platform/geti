FROM python:3.10-slim-bookworm@sha256:49454d2bf78a48f217eb25ecbcb4b5face313fea6a6e82706465a6990303ada2 AS base

# step 1: get cuda dependencies
FROM base AS cuda
ENV TORCH_EXTENSIONS_DIR=/.torch
ENV LIBRARY_PATH=/usr/local/cuda/lib64/stubs
ENV NCCL_VERSION=2.17.1
ENV CUDA_VERSION=12.1.1
ENV NV_CUDNN_VERSION=8.9.0.131-1
ENV NVIDIA_REQUIRE_CUDA=cuda>=12.1 brand=tesla,driver>=470,driver<471 brand=unknown,driver>=470,driver<471 brand=nvidia,driver>=470,driver<471 brand=nvidiartx,driver>=470,driver<471 brand=geforce,driver>=470,driver<471 brand=geforcertx,driver>=470,driver<471 brand=quadro,driver>=470,driver<471 brand=quadrortx,driver>=470,driver<471 brand=titan,driver>=470,driver<471 brand=titanrtx,driver>=470,driver<471 brand=tesla,driver>=525,driver<526 brand=unknown,driver>=525,driver<526 brand=nvidia,driver>=525,driver<526 brand=nvidiartx,driver>=525,driver<526 brand=geforce,driver>=525,driver<526 brand=geforcertx,driver>=525,driver<526 brand=quadro,driver>=525,driver<526 brand=quadrortx,driver>=525,driver<526 brand=titan,driver>=525,driver<526 brand=titanrtx,driver>=525,driver<526
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV NVIDIA_VISIBLE_DEVICES=all
ENV LD_LIBRARY_PATH=/usr/local/nvidia/lib:/usr/local/nvidia/lib64:/usr/local/lib
ENV PATH=/usr/local/nvidia/bin:/usr/local/cuda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV TORCH_CUDA_ARCH_LIST="6.0;6.1;6.2;7.0;7.2;7.5;8.0;8.6"
ENV TORCH_DONT_CHECK_COMPILER_ABI=1

RUN apt update \
	&& apt install -y wget --no-install-recommends

RUN wget https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64/cuda-keyring_1.1-1_all.deb \
    && dpkg -i cuda-keyring_1.1-1_all.deb \
    && rm -rf cuda-keyring_1.1-1_all.deb

RUN apt update \
	&& apt install -y --no-install-recommends \
    cuda-libraries-12-6 \
    cuda-compiler-12-6 \
    && apt clean all \
    && rm -rf /var/cache/apt/* \
	&& echo "/usr/local/nvidia/lib" >> /etc/ld.so.conf.d/nvidia.conf \
	&& echo "/usr/local/nvidia/lib64" >> /etc/ld.so.conf.d/nvidia.conf

# step 2: get python dependencies
FROM base AS build

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter across both images.
ENV UV_PYTHON_DOWNLOADS=0

# Copy the service dependencies
COPY --link --from=libs . libs

WORKDIR /interactive_ai/workflows/otx_domain/trainer/otx_v2

COPY --link --from=ghcr.io/astral-sh/uv:0.6.12@sha256:515b886e8eb99bcf9278776d8ea41eb4553a794195ef5803aa7ca6258653100d /uv /bin/uv

COPY --link scripts/ scripts
COPY --link run run
COPY --link download_pretrained_weights.py download_pretrained_weights.py

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-editable

# step 3: build final runtime image
FROM base AS runtime

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1=1.6.* \
    libglib2.0-0=2.74.* \
    curl && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -l -u 10001 non-root && \
	pip3 uninstall -y setuptools pip wheel && \
    rm -rf /root/.cache/pip

# Copy the application from the builder
COPY --link --from=build --chown=10001 /interactive_ai/workflows/otx_domain/trainer/otx_v2 /interactive_ai/workflows/otx_domain/trainer/otx_v2
COPY --link --from=cuda --chown=10001 /usr/local /usr/local

# Place executables in the environment at the front of the path
ENV PATH="/interactive_ai/workflows/otx_domain/trainer/otx_v2/.venv/bin:/interactive_ai/workflows/otx_domain/trainer/otx_v2:$PATH"
ENV PYTHONPATH="/interactive_ai/workflows/otx_domain/trainer/otx_v2"
ENV HF_HUB_OFFLINE=1

USER non-root
WORKDIR /home/non-root
WORKDIR /interactive_ai/workflows/otx_domain/trainer/otx_v2
