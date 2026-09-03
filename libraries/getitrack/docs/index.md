# getitrack documentation

getitrack is a standalone, framework-agnostic multi-object tracking (MOT) library for Geti. It turns a stream of per-frame object detections into stable, id-tagged tracks. It is detector agnostic: bring bounding boxes from any detection framework and get track ids back.

## Mental model

The library has one core loop. You feed it one frame's detections and it returns that frame's tracks:

```python
tracked = tracker.update(detections)
```

- `Detections` is what the detector saw this frame: boxes, scores, class ids. No identities.
- `TrackedDetections` is what the tracker decided: the same boxes plus a stable `track_id` and a lifecycle `track_state` per row.

The tracker holds its state across calls, so you construct it once and call `update` once per frame. Detection itself is external: you run your own detector, or wrap one in a `DetectionAdapter`, and hand the boxes to getitrack.

Both containers are plain numpy dataclasses with eager validation, defined in `core/detection.py`. getitrack has no dependency on the Geti training library getitune, so the same tracker runs inside the Geti application, through a detector adapter, or entirely on its own.

## Contents

| Page | What it covers |
| --- | --- |
| [Getting started](getting-started.md) | Install, construct a tracker, and run the per-frame loop. |
| [Concepts](concepts.md) | `Detections` vs `TrackedDetections`, the `Track` lifecycle, `frame_id`, embeddings. |
| [Algorithms](algorithms.md) | ByteTrack, SORT, OC-SORT, and choosing the association distance metric. |
| [Configuration](configuration.md) | Full `TrackerConfig` reference and YAML load and save. |
| [API reference](autoapi/getitrack/index) | Auto-generated from the source docstrings: every public module, class, and function. |
| [Roadmap](roadmap.md) | Features in flight or planned that are not yet merged. |

## Available algorithms

Three trackers are implemented and registered: ByteTrack (the default), SORT, and OC-SORT. See [Algorithms](algorithms.md). BoT-SORT and a memory tracker appear in the `AlgorithmType` enum but are not yet registered on this release; see [Roadmap](roadmap.md).

```{toctree}
:hidden:
:caption: Guide

getting-started
concepts
algorithms
configuration
roadmap
```

```{toctree}
:hidden:
:caption: API reference

autoapi/getitrack/index
```
