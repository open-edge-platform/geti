# syntax=docker/dockerfile:1.7

# Builder image
FROM dev-go as builder

WORKDIR /build/control_plane/auth_proxy

COPY --link go.mod .
COPY --link go.sum .

COPY --link --from=account_service_client . ../../../grpc_interfaces/grpc_interfaces/account_service/go

RUN go mod download

COPY --link . .
RUN CGO_ENABLED=0 go build -trimpath -mod=readonly -gcflags="all=-spectre=all" -asmflags="all=-spectre=all" -ldflags="all=-s -w" -a -o auth_proxy .

RUN ls -al .

# Production image
FROM debian_image AS auth_proxy

COPY --link --from=builder /build/control_plane/auth_proxy/auth_proxy /

RUN useradd -ms /bin/bash -l -u 10001 nonroot
USER nonroot

ENV GRPC_SERVER_PORT=7001
EXPOSE $GRPC_SERVER_PORT

ENV HTTP_SERVER_PORT=7002
EXPOSE $HTTP_SERVER_PORT

ENTRYPOINT ["./auth_proxy"]
