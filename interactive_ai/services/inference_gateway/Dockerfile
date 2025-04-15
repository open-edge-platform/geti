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

FROM golang:1.23.3 as ffmpeg

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg=7:5.1.6-0+deb12u1

FROM gcr.io/distroless/static-debian12:nonroot AS inference_gateway

COPY --from=ffmpeg /usr/bin/ffmpeg /usr/bin/ffmpeg
COPY --from=ffmpeg /usr/bin/ffprobe /usr/bin/ffprobe
COPY --from=ffmpeg /usr/lib/x86_64-linux-gnu /usr/lib/x86_64-linux-gnu
COPY --from=ffmpeg /usr/share/ffmpeg /usr/share/ffmpeg

COPY --link --from=builder /build/interactive_ai/service/inference_gateway /

USER nonroot

ENV GIN_MODE=release
ENV INFERENCE_GATEWAY_PORT=7000
EXPOSE $INFERENCE_GATEWAY_PORT

ENTRYPOINT ["./inference_gateway"]
