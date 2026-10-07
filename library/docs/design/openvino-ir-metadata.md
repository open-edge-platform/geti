<!-- Copyright (C) 2026 Intel Corporation -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# OpenVINO IR / ONNX export metadata (`rt_info["model_info"]`)

All keys are written under the `model_info` section of the OpenVINO IR `rt_info`
(or as `"model_info <key>"` entries in ONNX `metadata_props`). Values are strings.

For the values written by each model that Geti can train, see [model-ir-metadata-inventory.md](model-ir-metadata-inventory.md).

## Sources

| Source                                        | File                                                               | Content                                                 |
| --------------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------- |
| `TaskLevelExportParameters.to_metadata()`     | `library/src/getitune/types/export.py`                             | Task info, labels, postprocessing, tiling               |
| `ModelExporter._extend_model_metadata()`      | `library/src/getitune/backend/lightning/exporter/base.py`          | Preprocessing (normalization, resize, intensity)        |
| `HFModelExporter.metadata`                    | `library/src/getitune/backend/huggingface/exporter/hf_exporter.py` | Default intensity keys when no `IntensityConfig` is set |
| `ModelExporter._embed_openvino_ir_metadata()` | `library/src/getitune/backend/lightning/exporter/base.py`          | Writes all keys via `ov_model.set_rt_info()`            |

Where a key comes from both sources, the value from `to_metadata()` is used.

## Preprocessing parameters

Expected runtime order: **dtype handling → intensity mapping → channel repeat → channel swap → resize/pad → mean/scale normalization → layout NCHW**.

| Key                         | Type / values                                                        | When written                                               | Action at inference                                                                                                                                                                                                                    |
| --------------------------- | -------------------------------------------------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `input_dtype`               | `u8` \| `u16` \| `i16` \| `f32`                                      | Intensity config present (HF: always, defaults to `u8`)    | Accept and decode the input image with this storage dtype. Do not downcast high-bit-depth data to uint8.                                                                                                                               |
| `intensity_mode`            | `scale_to_unit` \| `window` \| `percentile` \| `range_scale`         | Intensity config present (HF: always)                      | Choose the intensity mapping that converts raw pixels to float32 `[0, 1]`. See the table below.                                                                                                                                        |
| `intensity_max_value`       | float                                                                | Intensity config with `max_value` set (HF default `255.0`) | Upper bound / divisor (`scale_to_unit`, `range_scale`).                                                                                                                                                                                |
| `intensity_window_center`   | float                                                                | `window_center` set                                        | Window center for the `window` mode.                                                                                                                                                                                                   |
| `intensity_window_width`    | float                                                                | `window_width` set                                         | Window width for the `window` mode.                                                                                                                                                                                                    |
| `intensity_percentile_low`  | float (default `1.0`)                                                | Intensity config present                                   | Lower quantile for the `percentile` mode.                                                                                                                                                                                              |
| `intensity_percentile_high` | float (default `99.0`)                                               | Intensity config present                                   | Upper quantile for the `percentile` mode.                                                                                                                                                                                              |
| `intensity_scale_factor`    | float (default `1.0`)                                                | Intensity config present                                   | Multiply raw pixels by this value before clipping (`range_scale`).                                                                                                                                                                     |
| `intensity_min_value`       | float (default `0.0`)                                                | Intensity config present                                   | Lower clip bound (`range_scale`).                                                                                                                                                                                                      |
| `intensity_repeat_channels` | `"True"`                                                             | `repeat_channels > 0`                                      | Repeat a single-channel image to 3 channels before feeding the model.                                                                                                                                                                  |
| `reverse_input_channels`    | `"True"` / `"False"`                                                 | Always                                                     | If `True`, swap BGR↔RGB before inference.                                                                                                                                                                                             |
| `resize_type`               | `standard` \| `crop` \| `fit_to_window` \| `fit_to_window_letterbox` | Always                                                     | `standard`: resize to the input size, ignoring aspect ratio. `crop`: resize then center-crop. `fit_to_window`: keep aspect ratio, fit inside the window. `fit_to_window_letterbox`: keep aspect ratio, fit, then pad to the full size. |
| `pad_value`                 | int (Lightning/HF `0`, Ultralytics `114`)                            | Always                                                     | Fill value for padded areas (letterbox / fit), in 8-bit pixel units.                                                                                                                                                                   |
| `mean_values`               | space-separated floats                                               | Always (may be empty)                                      | Subtract the per-channel mean: `x = x - mean`.                                                                                                                                                                                         |
| `scale_values`              | space-separated floats                                               | Always (may be empty)                                      | Divide by the per-channel scale (std): `x = x / scale`.                                                                                                                                                                                |

### Intensity modes

| `intensity_mode` | Action                                                                                                 |
| ---------------- | ------------------------------------------------------------------------------------------------------ |
| `scale_to_unit`  | `x = clip(x / max_value, 0, 1)` (`max_value` defaults to 255 for u8, 65535 for u16, 32767 for i16)     |
| `window`         | `lo = center - width/2`, `hi = center + width/2`; `x = (clip(x, lo, hi) - lo) / (hi - lo)`             |
| `percentile`     | `lo, hi = percentile(x, low), percentile(x, high)` per image; `x = (clip(x, lo, hi) - lo) / (hi - lo)` |
| `range_scale`    | `x = x * scale_factor`; `x = (clip(x, min_value, max_value) - min_value) / (max_value - min_value)`    |

## Postprocessing parameters

| Key                      | Type / values        | Tasks                                    | Action at inference                                                                                                                                                            |
| ------------------------ | -------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `multilabel`             | `"True"` / `"False"` | Classification                           | `True`: sigmoid on each class, keep classes ≥ `confidence_threshold`. `False`: softmax, keep the top-1 class.                                                                  |
| `output_raw_scores`      | `"True"` / `"False"` | Classification                           | Also return the full score vector for all classes.                                                                                                                             |
| `confidence_threshold`   | float                | Classification, Detection, Instance seg. | Drop predictions with a score below this value.                                                                                                                                |
| `iou_threshold`          | float                | Detection, Instance seg.                 | IoU threshold for NMS.                                                                                                                                                         |
| `nms_execute`            | `"True"` / `"False"` | Detection, Instance seg.                 | `True`: the model has no built-in NMS, so the runtime must run NMS (`iou_threshold`, `agnostic_nms`, `nms_max_predictions`). `False`: NMS is already in the graph, so skip it. |
| `agnostic_nms`           | `"True"` / `"False"` | Detection, Instance seg.                 | `True`: run NMS across all classes together. `False`: run NMS per class.                                                                                                       |
| `nms_max_predictions`    | int                  | Detection, Instance seg.                 | Keep at most N boxes after NMS.                                                                                                                                                |
| `return_soft_prediction` | `"True"` / `"False"` | Semantic seg.                            | Also return per-pixel class probability maps.                                                                                                                                  |
| `soft_threshold`         | float                | Semantic seg.                            | Pixels whose max class probability is below this become background or unassigned.                                                                                              |
| `blur_strength`          | int                  | Semantic seg.                            | Blur kernel size applied to the soft maps before argmax (smoother output).                                                                                                     |

## Tiling parameters

| Key               | Type        | Action at inference                                                                                                                  |
| ----------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `tile_size`       | int         | Split the input image into square tiles of this size and run the model on each tile (plus the full image, depending on the runtime). |
| `tiles_overlap`   | float (0–1) | Fraction of overlap between neighboring tiles.                                                                                       |
| `max_pred_number` | int         | Maximum number of predictions kept after merging the tiles (merge with NMS).                                                         |

## Model / label info (no pixel processing)

| Key                   | Action at inference                                                                                        |
| --------------------- | ---------------------------------------------------------------------------------------------------------- |
| `model_type`          | Choose the ModelAPI wrapper class (e.g. `Classification`, `YOLO11`).                                       |
| `task_type`           | Choose the task-specific result conversion.                                                                |
| `model_name`          | Informational.                                                                                             |
| `labels`              | Space-separated label names (spaces in names become `_`). Map output index → name.                         |
| `label_ids`           | Space-separated label IDs, in the same order as `labels`.                                                  |
| `label_info`          | Full JSON `LabelInfo` (hierarchy, groups). Use it for hierarchical or multi-group classification decoding. |
| `optimization_config` | JSON NNCF PTQ configuration. Used by the OpenVINO backend when quantizing; not used for inference.         |
| `getitune_version`    | Informational / compatibility check.                                                                       |

## Defaults per backend

| Backend      | Exporter                   | `resize_type`                    | `pad_value`               | mean / std                | Intensity                                      |
| ------------ | -------------------------- | -------------------------------- | ------------------------- | ------------------------- | ---------------------------------------------- |
| Lightning    | `LightningModelExporter`   | Set per model (often `standard`) | Set per model (often `0`) | Model's `DataInputParams` | Only if `IntensityConfig` is set               |
| Hugging Face | `HFModelExporter`          | `standard`                       | `0`                       | Model's `DataInputParams` | Falls back to `u8` + `scale_to_unit` + `255.0` |
| Ultralytics  | `UltralyticsModelExporter` | `fit_to_window_letterbox`        | `114`                     | `0,0,0` / `1,1,1`         | `scale_to_unit`, `uint8`                       |

Ultralytics also writes `nms_execute = not export_nms` and a separate `metadata.yaml` (for the Ultralytics CLI, not `rt_info`).
