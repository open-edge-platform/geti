# syntax=docker/dockerfile:1.7

# Builder image
FROM golang:1.23.8@sha256:ec5612bbd9e96d5b80a8b968cea06a4a9b985fe200ff6da784bf607063273c59 AS build

WORKDIR /build/interactive_ai/service

COPY --link --from=iai_core . ../../libs/iai_core_go

RUN --mount=type=cache,target=/go/pkg/mod/ \
    --mount=type=bind,source=go.sum,target=go.sum \
    --mount=type=bind,source=go.mod,target=go.mod \
    go mod download -x

RUN --mount=type=cache,target=/go/pkg/mod/ \
    --mount=type=bind,source=go.sum,target=go.sum \
    --mount=type=bind,source=go.mod,target=go.mod \
    --mount=type=bind,source=main.go,target=main.go \
    --mount=type=bind,source=app,target=app \
	CGO_ENABLED=0 go build -trimpath -mod=readonly -gcflags="all=-spectre=all" -asmflags="all=-spectre=all" -ldflags="all=-s -w" -a -o media_ms .

# Production image
FROM gcr.io/distroless/static-debian12:nonroot@sha256:627d6c5a23ad24e6bdff827f16c7b60e0289029b0c79e9f7ccd54ae3279fb45f AS runtime

COPY --link --from=build /build/interactive_ai/service/media_ms .

USER nonroot

ENV GIN_MODE=release
ENV PORT=5002
EXPOSE $PORT

ENTRYPOINT ["./media_ms"]
