# getitrack

Multi-object tracking toolkit.

getitrack turns per frame detections into stable object tracks. It is detector agnostic: bring bounding boxes from any detection framework and get track ids back.

## Documentation

See [docs/index.md](docs/index.md) for the guide and API reference: getting started, core concepts, the tracking algorithms, the configuration reference, and the full API.

## Installation

```bash
pip install getitrack
```

For development:

```bash
just venv
```

## Development

```bash
just lint        # ruff + pyrefly
just test-unit   # pytest
```

## License

Apache License 2.0. See [LICENSE](../../LICENSE) for details.
