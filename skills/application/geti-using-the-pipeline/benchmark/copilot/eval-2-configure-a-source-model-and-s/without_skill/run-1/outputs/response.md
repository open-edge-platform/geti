# Configuring a Source, Model, and Sink for a Geti Project's Live Inference Pipeline

Assumes the Geti backend is reachable at `http://<host>:<port>` and you already have a `project_id`
(and, for the model step, an existing trained/optimized model in that project). Replace placeholders
accordingly. All pipeline-related endpoints live under `/api/projects/{project_id}/pipeline`, while
sources and sinks are project-independent, reusable resources under `/api/sources` and `/api/sinks`.

## 1. Create a source

Sources describe where frames come from (USB camera, IP camera, video file, or an images folder).

```bash
curl -X POST http://<host>:<port>/api/sources \
  -H "Content-Type: application/json" \
  -d '{
        "source_type": "ip_camera",
        "name": "Line 3 Camera",
        "stream_url": "rtsp://192.168.1.100:554/stream1",
        "auth_required": false
      }'
```

Response (`201 Created`) returns a `SourceView` with an `id` — save it (e.g. `SOURCE_ID`).

Other supported `source_type` values: `usb_camera` (`device_id`), `video_file` (`video_path`, `loop`),
`images_folder` (`folder_path`, `ignore_existing_images`).

Optionally verify connectivity before wiring it into the pipeline:

```bash
curl -X POST http://<host>:<port>/api/sources/$SOURCE_ID:test
```

## 2. Create a sink

Sinks describe where predictions/frames get delivered (local folder or MQTT broker). A sink is
optional — if you skip it, predictions are still viewable via the WebRTC live-view stream.

```bash
curl -X POST http://<host>:<port>/api/sinks \
  -H "Content-Type: application/json" \
  -d '{
        "sink_type": "folder",
        "name": "Line 3 Output",
        "folder_path": "/data/output/line3",
        "output_formats": ["image_with_predictions", "predictions"],
        "rate_limit": 0.2
      }'
```

Save the returned `id` (`SINK_ID`). MQTT sinks use `broker_host`, `broker_port`, and `topic` instead
of `folder_path`. You can test connectivity the same way as sources:

```bash
curl -X POST http://<host>:<port>/api/sinks/$SINK_ID:test
```

## 3. Pick the model

List the models already trained/imported in the project to get a `model_id`:

```bash
curl http://<host>:<port>/api/projects/$PROJECT_ID/models
```

Pick the model you want to serve from the response and note its `id` (`MODEL_ID`). Only OpenVINO
model variants can run inference; if you don't pass a `model_variant_id`, the pipeline automatically
selects the default FP16 OpenVINO variant for that model.

## 4. Wire source + model + sink into the pipeline

`PATCH` the project's pipeline with all three references in one call (or do it incrementally):

```bash
curl -X PATCH http://<host>:<port>/api/projects/$PROJECT_ID/pipeline \
  -H "Content-Type: application/json" \
  -d '{
        "source_id": "'"$SOURCE_ID"'",
        "sink_id": "'"$SINK_ID"'",
        "model_id": "'"$MODEL_ID"'"
      }'
```

Useful optional fields in the same PATCH body:
- `"device": "cpu" | "xpu" | "cuda" | "xpu-1" | ...` — inference device.
- `"inference": {"confidence_threshold": 0.7}` — override the model's default confidence threshold
  (pass `null` to reset to the model's built-in value).
- `"model_variant_id"` — pin a specific OpenVINO variant instead of the default FP16 one.

This returns the updated `PipelineView` (still `status: "idle"` at this point — configuring the
pipeline doesn't start it).

## 5. Enable live inference

```bash
curl -X POST http://<host>:<port>/api/projects/$PROJECT_ID/pipeline:enable
```

This returns `204 No Content` on success and flips the pipeline to `RUNNING`: it starts pulling
frames from the source, running them through the model, and pushing results to the sink (if any).

A `409 Conflict` typically means another project's pipeline is already active on a device that only
supports one active pipeline at a time, or the configured folder sink isn't accessible — check the
error detail and either disable the conflicting pipeline (`POST /api/projects/{other_id}/pipeline:disable`)
or fix the sink path first.

To stop it later: `POST /api/projects/$PROJECT_ID/pipeline:disable`.

## 6. Verify it's running

**Check overall pipeline state:**
```bash
curl http://<host>:<port>/api/projects/$PROJECT_ID/pipeline
```
Look at `"status"` — it should be `"running"`.

**Check detailed component health** (source/sink/model connectivity, not just the on/off flag):
```bash
curl http://<host>:<port>/api/projects/$PROJECT_ID/pipeline/health
```
Returns `status: "running" | "error" | "idle"` plus a `components` breakdown with per-component
`status`/`message`/`updated_at` for `source`, `sink`, and `model`. If any component is unreachable
(e.g., camera disconnected, broker down), the overall status flips to `"error"` and the offending
component's message tells you why.

**Check throughput/latency metrics** (confirms frames are actually flowing, not just that the
pipeline is nominally "on"):
```bash
curl "http://<host>:<port>/api/projects/$PROJECT_ID/pipeline/metrics?time_window=60"
```
Returns average/min/max/p95/latest inference latency and throughput over the requested window
(default 60s, max 3600s). Non-zero throughput with reasonable latency confirms live inference is
actively processing data end to end.

**Watch it live:** the pipeline also feeds a WebRTC stream (`/api/webrtc/...`) that a front-end can
use to visualize predictions in real time, independent of whether a sink is configured — useful as a
visual sanity check that predictions are being produced.

## Summary of calls
1. `POST /api/sources` → `SOURCE_ID`
2. `POST /api/sinks` → `SINK_ID`
3. `GET /api/projects/{project_id}/models` → `MODEL_ID`
4. `PATCH /api/projects/{project_id}/pipeline` with `source_id`, `sink_id`, `model_id`
5. `POST /api/projects/{project_id}/pipeline:enable`
6. Verify: `GET /api/projects/{project_id}/pipeline` (status), `GET .../pipeline/health` (component
   health), `GET .../pipeline/metrics` (throughput/latency)
