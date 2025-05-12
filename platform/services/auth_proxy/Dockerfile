# syntax=docker/dockerfile:1.7

# Builder image
FROM golang:1.23.8 AS build

WORKDIR /build/control_plane/auth_proxy

COPY --link --from=account_service_client . ../../../libs/grpc_interfaces/src/grpc_interfaces/account_service/go

RUN --mount=type=cache,target=/go/pkg/mod/ \
    --mount=type=bind,source=go.sum,target=go.sum \
    --mount=type=bind,source=go.mod,target=go.mod \
    go mod download -x

RUN --mount=type=cache,target=/go/pkg/mod/ \
    --mount=type=bind,source=go.sum,target=go.sum \
    --mount=type=bind,source=go.mod,target=go.mod \
    --mount=type=bind,source=main.go,target=main.go \
    --mount=type=bind,source=app,target=app \
	CGO_ENABLED=0 go build -trimpath -mod=readonly -gcflags="all=-spectre=all" -asmflags="all=-spectre=all" -ldflags="all=-s -w" -a -o auth_proxy .

# Production image
FROM gcr.io/distroless/static-debian12:nonroot AS runtime

COPY --link --from=build /build/control_plane/auth_proxy/auth_proxy .

USER nonroot

ENV GRPC_SERVER_PORT=7001
EXPOSE $GRPC_SERVER_PORT

ENV HTTP_SERVER_PORT=7002
EXPOSE $HTTP_SERVER_PORT

ENTRYPOINT ["./auth_proxy"]
