# Roadmap

This release includes the ByteTrack, SORT, OC-SORT, and BoT-SORT trackers, the
configurable association distance metrics, track interpolation post-processing,
and the tracker state accessors. The features below are in progress or planned.

## In progress (not yet submitted)

- CLI and MOT evaluation module. A Typer CLI (`track`, `eval`) plus MOT metrics (MOTA, IDF1, ID switches) built on motmetrics.
- Deep OC-SORT and StrongSORT, built on the BoT-SORT appearance and GMC foundation.
- A memory-bank tracker, which will register the `memory` value in `AlgorithmType`.

## Planned

- Live and streaming video support: a frame-source abstraction, a streaming driver, a `TrackingPipeline` composing tracker and interpolator, and incremental (online) interpolation.
- Deeper Geti application integration for the detect-then-track pipeline and live inference.
- Hyperparameter tuning for recommended per-dataset defaults.

## Notes on the current enums

`AlgorithmType` lists `memory` ahead of the code that consumes it. Selecting `memory` on this release raises an "unknown algorithm" error because it is not registered yet. ByteTrack, SORT, OC-SORT, and BoT-SORT are all registered and selectable, and the `InterpolationConfig` fields on `TrackerConfig` drive the interpolation stage.
