# Creating a Geti detection project, uploading/annotating an image, and starting training via the REST API

Assuming the Geti FastAPI backend is running locally (e.g. `http://localhost:8000`), here is the end-to-end sequence of REST calls.

## 1. Create the detection project

```
POST /api/projects
Content-Type: application/json

{
  "name": "grapes",
  "task": {
    "task_type": "detection",
    "exclusive_labels": true,
    "labels": [
      { "name": "Chardonnay" },
      { "name": "Sauvignon Blanc" },
      { "name": "Cabernet Franc" }
    ]
  }
}
```

Response: `201 Created` with a `ProjectView` payload, e.g.:

```json
{
  "id": "7b073838-99d3-42ff-9018-4e901eb047fc",
  "name": "grapes",
  "task": {
    "task_type": "detection",
    "exclusive_labels": true,
    "labels": [
      { "id": "d476573e-d43c-42a6-9327-199a9aa75c33", "name": "Chardonnay", "color": "#A1B2C3" },
      { "id": "bbb782b7-8322-44e8-b6a9-90a5c9ee4bad", "name": "Sauvignon Blanc", "color": "#..." },
      { "id": "...", "name": "Cabernet Franc", "color": "#..." }
    ]
  },
  "active_pipeline": false,
  "created_at": "..."
}
```

Save `project.id` and each label's `id` — you need them for the next steps.

## 2. Upload an image to the project's dataset

```
POST /api/projects/{project_id}/dataset/media
Content-Type: multipart/form-data

file=@image.jpg
```

curl example:

```bash
curl -X POST "http://localhost:8000/api/projects/7b073838-99d3-42ff-9018-4e901eb047fc/dataset/media" \
  -F "file=@image.jpg"
```

Response: `201 Created` with a `MediaView` payload including the new media's `id` (this doubles as the dataset item id for images), e.g.:

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "image",
  "type": "image",
  ...
}
```

## 3. Annotate the image

Add one or more bounding-box annotations referencing the label ids from step 1:

```
POST /api/projects/{project_id}/dataset/media/{media_id}/annotations
Content-Type: application/json

{
  "annotations": [
    {
      "labels": [{ "id": "d476573e-d43c-42a6-9327-199a9aa75c33" }],
      "shape": { "type": "rectangle", "x": 10, "y": 20, "width": 100, "height": 200 }
    }
  ]
}
```

Response: `201 Created` with the resulting `MediaAnnotations`. (Use `GET` on the same path to review existing annotations, or `DELETE` to clear them.)

## 4. Start a training job

Query available model architectures and training devices first (optional but recommended):

```
GET /api/model_architectures?task=detection
GET /api/system/devices/training
```

Then submit the training job:

```
POST /api/jobs
Content-Type: application/json

{
  "job_type": "train",
  "project_id": "7b073838-99d3-42ff-9018-4e901eb047fc",
  "parameters": {
    "device": "cpu",
    "model_architecture_id": "object-detection-atss-mobilenet-v2",
    "parent_model_revision_id": null,
    "dataset_revision_id": null
  }
}
```

Response: `202 Accepted` with a `JobView`, e.g.:

```json
{
  "id": "e1c2...",
  "job_type": "train",
  "status": "pending",
  ...
}
```

## 5. Track job status

Poll the job or stream status updates:

```
GET /api/jobs/{job_id}                # one-shot status check
GET /api/jobs/{job_id}/status         # Server-Sent Events stream of status updates
GET /api/jobs/{job_id}/logs           # Server-Sent Events stream of job logs
```

Cancel if needed with `POST /api/jobs/{job_id}:cancel`.

## Summary of endpoints used

| Step | Method | Path |
|---|---|---|
| Create project | POST | `/api/projects` |
| Upload image | POST | `/api/projects/{project_id}/dataset/media` |
| Annotate image | POST | `/api/projects/{project_id}/dataset/media/{media_id}/annotations` |
| List architectures (optional) | GET | `/api/model_architectures?task=detection` |
| List training devices (optional) | GET | `/api/system/devices/training` |
| Start training | POST | `/api/jobs` |
| Check job status | GET | `/api/jobs/{job_id}` or `/api/jobs/{job_id}/status` |

Notes:
- Only one label is required per bounding box for an exclusive-label detection project; multiple boxes/labels can be included in a single annotations request.
- `dataset_revision_id: null` in the training request tells the backend to train on the latest dataset snapshot rather than a pinned historical revision.
- `parent_model_revision_id: null` starts training from scratch instead of fine-tuning an existing model.
