# Algorithms

Four trackers are implemented and registered. All share the `TrackerConfig` base (score floor, class filter, lifecycle, motion, distance metric) and add their own parameters. Select one with the `algorithm` key; see [Configuration](configuration.md) for every field.

## ByteTrack (default)

`ByteTrackTracker` (`algorithms/bytetrack.py:44`), config `ByteTrackConfig`. Reference: Zhang et al., "ByteTrack: Multi-Object Tracking by Associating Every Detection Box" (ECCV 2022).

Two-stage association. High-score detections are matched to predicted track boxes first; then the still-unmatched tracks get a second pass against the low-score detections, which recovers objects during brief low-confidence dips (occlusion, motion blur). Motion is a per-track Kalman filter; matching is class-aware when `match_class_only` is set.

Choose ByteTrack as the general-purpose default. It handles crowded scenes and flickering confidence well.

Key parameters: `high_score_threshold` (the high and low split, default 0.5), `match_threshold` (max assignment cost, default 0.8), `match_class_only`.

## SORT

`SortTracker` (`algorithms/sort.py`), config `SortConfig`. Reference: Bewley et al., "Simple Online and Realtime Tracking" (ICIP 2016).

Single-stage IoU association. Each frame advances every track's Kalman state, matches detections above the score floor to the predicted boxes with a Hungarian assignment on IoU cost, updates matched tracks, ages unmatched ones, and spawns a new track per unmatched detection.

Choose SORT as a fast, minimal baseline when detections are dense and reliable and you do not need the low-score recovery stage.

Key parameters: `iou_threshold` (minimum IoU for a match, default 0.3; the internal `match_threshold` is `1 - iou_threshold`), `match_class_only`.

## OC-SORT

`OCSortTracker` (`algorithms/ocsort.py`), config `OCSortConfig`. Reference: Cao et al., "Observation-Centric SORT" (CVPR 2023).

Extends SORT's motion-only tracking with three observation-centric mechanisms: OCM (a velocity-direction consistency term added to the first association cost), OCR (a recovery pass matching leftover detections against each track's last observation rather than its Kalman prediction), and ORU (on re-acquisition after a gap, the filter is rewound to the last observation and replayed along a virtual trajectory). An optional BYTE stage associates low-score detections when `use_byte` is set.

Choose OC-SORT for non-linear motion and longer occlusions, where SORT's straight-line Kalman prediction drifts.

Key parameters: `det_threshold` (high-score gate, default 0.6), `iou_threshold` (default 0.3), `delta_t` (frame gap for the momentum estimate, default 3), `inertia` (weight of the OCM term, default 0.2), `use_byte`.

## BoT-SORT

`BotSortTracker` (`algorithms/botsort.py`), config `BotSortConfig` (extends `ByteTrackConfig`). Reference: Aharon et al., "BoT-SORT: Robust Associations Multi-Pedestrian Tracking" (2022).

Extends ByteTrack with two additions. Appearance (ReID): box crops are embedded by a torchreid model (run natively via the `torch` backend or as an OpenVINO IR via the `openvino` backend), and the appearance cost is fused into the IoU cost on the high-score stage, gated by an IoU floor so appearance never rescues non-overlapping boxes. Each track keeps a small gallery of admitted descriptors. Camera-motion compensation (GMC): the affine frame-to-frame motion is estimated (sparse optical flow, ECC, ORB, or SIFT) and applied to the Kalman states before association, so ego-motion does not break matches.

Choose BoT-SORT when identities must survive occlusions or crossings that motion and IoU alone cannot disambiguate, and you can afford the ReID model. It needs the `reid` extra (`pip install "getitrack[reid]"`).

Key parameters: `appearance_weight` (weight of the appearance term, default 0.25), `appearance_iou_floor` (minimum IoU for appearance to apply, default 0.5), `gallery_size` (descriptors kept per track, default 50), `appearance_threshold` (max cosine distance to admit a descriptor, default 0.25), plus the `reid` and `gmc` configuration blocks.

## Choosing the association distance metric

Every tracker uses `TrackerConfig.distance_metric` (default `iou`) to score detection-to-track pairs. The cost is `1 - metric`, so a lower cost is a better match. The four metrics are in `matching/distance/` and resolved through `BaseDistanceMetric.from_metric`.

| Metric | Cost range | When it helps |
| --- | --- | --- |
| iou | [0, 1] | The reference. Saturates at 1 for any non-overlapping pair, so it cannot rank disjoint boxes. |
| giou | [0, ~2] | Adds an enclosing-box penalty, so it stays informative past zero overlap. |
| diou | [0, ~2] | Adds a centre-distance term; prefers boxes whose centres are close. |
| ciou | [0, ~2.31] | Extends DIoU with an aspect-ratio consistency term. |

The extended metrics only add value above a cost of 1, so raise the match threshold when you select one. `ByteTrackConfig.match_threshold` already allows up to 2.5 for this reason; the SORT and OC-SORT `match_threshold` is derived from `iou_threshold` and is calibrated for IoU. Retune thresholds when moving away from `iou`.
