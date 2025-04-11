# syntax=docker/dockerfile:1.7

# Builder image
FROM dev-go as builder

WORKDIR /build/interactive_ai/service

COPY --link go.mod .
COPY --link go.sum .
COPY --link --from=go_sdk . ../../libs/go_sdk
COPY --link --from=modelmesh . ../../../grpc_interfaces/grpc_interfaces/model_mesh/go/pb
COPY --link --from=modelregistration . ../../../grpc_interfaces/grpc_interfaces/model_registration/go/pb
COPY --link --from=predict . ../../../grpc_interfaces/grpc_interfaces/predict/go/pb
RUN go mod download

COPY --link . .
RUN CGO_ENABLED=0 go build -trimpath -mod=readonly -gcflags="all=-spectre=all" -asmflags="all=-spectre=all" -ldflags="all=-s -w" -a -o inference_gateway .

RUN ls -al .

# Production image
FROM debian_image AS inference_gateway

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg=7:5.1.6-0+deb12u1 && \
    rm -rf /var/lib/apt/lists/*

COPY --link --from=builder /build/interactive_ai/service/inference_gateway /

RUN useradd -ms /bin/bash -l -u 10001 nonroot
USER nonroot

ENV GIN_MODE=release
ENV INFERENCE_GATEWAY_PORT=7000
EXPOSE $INFERENCE_GATEWAY_PORT

ENTRYPOINT ["./inference_gateway"]
