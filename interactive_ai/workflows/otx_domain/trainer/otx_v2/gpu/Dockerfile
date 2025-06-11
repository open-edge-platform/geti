FROM python:3.10-slim-bookworm@sha256:2ee0fb8794bf82af1b2db168ada5869b4c27d17720dd3b155b56c111fb4a38ae AS base

# Set environment variables
ENV TORCH_EXTENSIONS_DIR=/.torch \
    LIBRARY_PATH=/usr/local/cuda/lib64/stubs \
    NCCL_VERSION=2.17.1 \
    CUDA_VERSION=12.1.1 \
    NV_CUDNN_VERSION=8.9.0.131-1 \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    NVIDIA_VISIBLE_DEVICES=all \
    LD_LIBRARY_PATH=/usr/local/nvidia/lib:/usr/local/nvidia/lib64:/usr/local/lib \
    PATH=/usr/local/nvidia/bin:/usr/local/cuda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    TORCH_CUDA_ARCH_LIST="6.0;6.1;6.2;7.0;7.2;7.5;8.0;8.6" \
    TORCH_DONT_CHECK_COMPILER_ABI=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    HF_HUB_OFFLINE=1

# Install CUDA dependencies
RUN apt update && \
    apt install -y wget --no-install-recommends && \
    wget https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64/cuda-keyring_1.1-1_all.deb && \
    dpkg -i cuda-keyring_1.1-1_all.deb && \
    rm -rf cuda-keyring_1.1-1_all.deb && \
    apt update && \
    apt install -y --no-install-recommends \
        cuda-libraries-12-6 \
        cuda-compiler-12-6 && \
    apt clean all && \
    rm -rf /var/cache/apt/* && \
    echo "/usr/local/nvidia/lib" >> /etc/ld.so.conf.d/nvidia.conf && \
    echo "/usr/local/nvidia/lib64" >> /etc/ld.so.conf.d/nvidia.conf

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

# Copy application files
COPY --link --from=libs . libs
WORKDIR /interactive_ai/workflows/otx_domain/trainer/otx_v2
COPY --link scripts/ scripts
COPY --link run run
COPY --link download_pretrained_weights.py download_pretrained_weights.py
COPY --link uv.lock uv.lock
COPY --link pyproject.toml pyproject.toml

# Install Python dependencies
COPY --link --from=ghcr.io/astral-sh/uv:0.6.12@sha256:515b886e8eb99bcf9278776d8ea41eb4553a794195ef5803aa7ca6258653100d /uv /bin/uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# Set environment paths
ENV PATH="/interactive_ai/workflows/otx_domain/trainer/otx_v2/.venv/bin:/interactive_ai/workflows/otx_domain/trainer/otx_v2:$PATH" \
    PYTHONPATH="/interactive_ai/workflows/otx_domain/trainer/otx_v2"

# Set user and working directory
USER non-root
WORKDIR /home/non-root
WORKDIR /interactive_ai/workflows/otx_domain/trainer/otx_v2
