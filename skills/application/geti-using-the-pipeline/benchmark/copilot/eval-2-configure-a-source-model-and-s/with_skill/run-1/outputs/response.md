# Configuring a source, model, and sink, then enabling live inference

This walks through wiring up the inference pipeline for a project that already
has at least one trained model, and how to confirm it's actually running
afterwards.

Before starting: I need your Geti instance's base URL (e.g. `https://localhost:7860`
for a local dev/Docker/MSIX install — this is only the default, not a given, so
tell me if yours differs) and the `project_id` you want to configure. All calls
below assume that base URL and are against the REST API served by the FastAPI
backend. The authoritative contract for these endpoints is whatever your
instance serves at `GET /api/openapi.json` — if anything here looks off versus
that spec, trust the spec.

## 1. Create (or pick) a source

`POST /api/sources` — the required fields depend on `source_type`. Common examples:

**USB camera**
```json
{
  "source_type": "usb_camera",
  "name": "USB Camera 1",
  "device_id": 0
}
```

**IP/RTSP camera**
```json
{
  "source_type": "ip_camera",
  "name": "IP Camera 1",
  "stream_url": "rtsp://192.168.1.100:554/stream1",
  "auth_required": true
}
```

**Video file** (`video_path`, optional `loop`) or **images folder**
(`folder_path`, optional `ignore_existing_images`) are also supported.

The response is a `SourceView` with an `id` — save it. If you already created a
source earlier, `GET /api/sources` lists existing ones instead of creating a
new one.

Optionally sanity-check reachability before wiring it into a pipeline:
`POST /api/sources/{source_id}:test` → connectivity result.

## 2. Create (or pick) a sink

`POST /api/sinks` — again the fields depend on `sink_type`:

**Local folder**
```json
{
  "sink_type": "folder",
  "name": "My Output Folder",
  "folder_path": "/path/to/output",
  "output_formats": ["image_with_predictions"],
  "rate_limit": 0.2
}
```

**MQTT broker**
```json
{
  "sink_type": "mqtt",
  "name": "Local MQTT Broker",
  "broker_host": "localhost",
  "broker_port": 1883,
  "topic": "predictions",
  "output_formats": ["predictions"]
}
```

Save the returned `id`. `GET /api/sinks` lists existing sinks, and
`POST /api/sinks/{sink_id}:test` checks connectivity (e.g. that the folder is
writable or the broker is reachable) before you rely on it.

A sink is optional — you can skip it and only view predictions through the
WebRTC visualization stream, but since the task calls for one, wire it in
below.

## 3. Pick the trained model

`GET /api/projects/{project_id}/models` lists the models trained for this
project; grab the `id` of the one you want live. You don't need a
`model_variant_id` — when omitted, the pipeline defaults to the model's FP16
OpenVINO variant. Only OpenVINO variants can run inference, so if you do pass
`model_variant_id` explicitly, make sure it's an OpenVINO export (and check the
device supports INT8 if that's the variant you pick).

## 4. Bind source, model, and sink into the pipeline

`PATCH /api/projects/{project_id}/pipeline`:

```json
{
  "source_id": "<source id from step 1>",
  "model_id": "<model id from step 3>",
  "sink_id": "<sink id from step 2>"
}
```

This is a partial update — you can send just these three fields even if the
pipeline already has other settings (device, data collection policies,
confidence threshold, etc.) configured. Response is a `PipelineView` reflecting
the new wiring. If you also want to pin the inference device (e.g. `"cpu"`,
`"xpu"`) or set a custom confidence threshold, add `"device"` or
`"inference": {"confidence_threshold": 0.7}` to the same request.

## 5. Enable live inference

```
POST /api/projects/{project_id}/pipeline:enable
```

Returns `204 No Content` on success. This flips the pipeline to `RUNNING`: it
starts pulling frames from the source, running them through the bound model,
and forwarding results to the sink. A `409 Conflict` here usually means either
another project's pipeline is already active on a device that only supports
one active pipeline at a time, or the sink isn't reachable (e.g. folder sink
path not writable) — check the source/sink `:test` endpoints if that happens.

Use `POST /api/projects/{project_id}/pipeline:disable` (also `204`) any time
you want to stop it again without deleting the configuration.

## 6. Verify it's actually running

Several ways to confirm, roughly in order of how much detail they give you:

1. **Quick status check** — `GET /api/projects/{project_id}/pipeline` and
   confirm the `status` field reads `RUNNING` (not `IDLE`) and that
   `source_id`, `sink_id`, and `model_id` match what you just configured.
2. **Health/connectivity check** — `GET /api/projects/{project_id}/pipeline/health`.
   This reports per-component status (source, sink, inference) and rolls them
   up into an overall status of `RUNNING`, `ERROR`, or `IDLE`. If anything is
   `ERROR`, that tells you which leg of the pipeline (source, sink, or model)
   is the problem.
3. **Live metrics** — `GET /api/projects/{project_id}/pipeline/metrics?time_window=60`
   returns inference latency (avg/min/max/p95/latest) and throughput over the
   requested window (seconds, up to 3600). Non-zero throughput and a sane
   latency number are the clearest sign frames are actually being processed
   end-to-end.
4. **Check the sink's actual output** — e.g. list files landing in the
   configured folder, or subscribe to the MQTT topic, to confirm predictions
   are reaching the destination and not just being computed.
5. Optionally, `POST /api/projects/{project_id}/pipeline:capture` grabs the
   next processed frame into the project's dataset — useful both as a
   verification step and to start building a retraining set from live data.

If you tell me the base URL and project ID, I can walk through the actual
calls with you instead of the generic templates above.
