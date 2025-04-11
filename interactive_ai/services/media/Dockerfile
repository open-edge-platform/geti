# syntax=docker/dockerfile:1.7

# Builder image
FROM dev-go as builder

WORKDIR /build/interactive_ai/service

COPY --link go.mod .
COPY --link go.sum .
COPY --link --from=go_sdk . ../../libs/go_sdk
RUN go mod download

COPY --link . .
RUN CGO_ENABLED=0 go build -trimpath -mod=readonly -gcflags="all=-spectre=all" -asmflags="all=-spectre=all" -ldflags="all=-s -w" -a -o media_ms .

RUN ls -al .

# Production image
FROM debian_image AS media

COPY --link --from=builder /build/interactive_ai/service/media_ms /

RUN useradd -ms /bin/bash -l -u 10001 nonroot
USER nonroot

ENV GIN_MODE=release
ENV PORT=5002
EXPOSE $PORT

ENTRYPOINT ["./media_ms"]
