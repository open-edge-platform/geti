# Account Service

## Development

### Toolchain installation

1. [Install Go](https://go.dev/doc/install) (version `1.20.5` as of this document's creation date).
1. Get Google API Protocol Buffer specifications (pinned to ref `499a1f532e348dc3dbbeda9b6e65c5b4b0553517`).
    ```bash
    mkdir -p /tmp/googleapis && \
      cd /tmp/googleapis && \
      wget https://github.com/googleapis/googleapis/archive/499a1f532e348dc3dbbeda9b6e65c5b4b0553517.zip -O googleapis.zip && \
      unzip googleapis.zip && \
      sudo cp -R googleapis-499a1f532e348dc3dbbeda9b6e65c5b4b0553517/google /usr/local/include && \
      cd .. && \
      rm -r /tmp/googleapis
    ```
1. Navigate to Account Service's root directory (containing this `README.md` document) and download the dependencies.
    ```bash
    go get
    ```
