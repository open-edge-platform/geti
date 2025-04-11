# syntax=docker/dockerfile:1.7

# Builder image
FROM dev-go as builder

WORKDIR /build/control_plane/account_service

COPY --link go.mod .
COPY --link go.sum .
COPY app/common /build/control_plane/account_service/app/common
COPY --link --from=credit_system . ../../../grpc_interfaces/grpc_interfaces/credit_system/go
COPY --link --from=account_service_grpc . ../../../grpc_interfaces/grpc_interfaces/account_service/go

RUN go mod download

COPY --link . .
RUN CGO_ENABLED=0 go build -trimpath -mod=readonly -gcflags="all=-spectre=all" -asmflags="all=-spectre=all" -ldflags="all=-s -w" -a -o account_service .

# Production image
FROM debian_image AS account_service

COPY --link --from=builder /build/control_plane/account_service/account_service /

RUN useradd -ms /bin/bash -l -u 10001 nonroot
USER nonroot

ENV GRPC_SERVER_PORT=5001
EXPOSE $GRPC_SERVER_PORT

ENV GATEWAY_SERVER_PORT=5002
EXPOSE $GATEWAY_SERVER_PORT

ENTRYPOINT ["./account_service"]

