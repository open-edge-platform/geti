include ../../../Makefile.shared-python

DOCKER_BUILD_CONTEXT := --build-context libs=../../../libs \
						--build-context sc_sdk=../../../interactive_ai/libs/sc_sdk \
						--build-context grpc_interfaces=../../../grpc_interfaces \

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg=7:5.1.6-0+deb12u1 && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -l -u 10001 non-root && \
	pip3 uninstall -y setuptools pip wheel && \
    rm -rf /root/.cache/pip