# syntax=docker/dockerfile:1.7

FROM python:3.10-slim-bookworm@sha256:49454d2bf78a48f217eb25ecbcb4b5face313fea6a6e82706465a6990303ada2

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0

COPY --from=ghcr.io/astral-sh/uv:0.6.12@sha256:515b886e8eb99bcf9278776d8ea41eb4553a794195ef5803aa7ca6258653100d /uv /uvx /bin/

ARG DOCKER_VERSION="5:28.0.4-1~debian.12~bookworm"

ENV DOCKER_VERSION=${DOCKER_VERSION}

RUN apt update \
    && apt --no-install-recommends -y install \
        ca-certificates curl \
        build-essential=12.* \
        git=1:2.39.* \
        libldap2-dev libsasl2-dev libgl1 libglib2.0-0 ffmpeg \
    # Add Docker's official GPG key
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    # Add the repository to Apt sources
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt update \
    && apt -y install docker-ce-cli=${DOCKER_VERSION} \
    && apt clean all \
    && rm -rf /var/cache/apt/*

RUN groupadd docker \
    && useradd -l -m -u 1001 builder \
    && usermod -aG docker builder \
    && mkdir -p /home/builder/.docker \
    && chown builder:builder /home/builder/.docker
WORKDIR /app
USER builder
