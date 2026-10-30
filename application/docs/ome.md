# OME-\* Format Support (OME-TIFF now, OME-Zarr later)

- Scope: `application/backend/` (primary), `application/ui/` (separate workstream), `libraries/getitune/` (no change)
- Supersedes: nothing
- Related docs: [`entities.md`](../entities.md), [`dataset.md`](../dataset.md), [`migration-guidelines.md`](../migration-guidelines.md)

---

## 1. Context

Geti currently models a dataset as flat 2D media: `Image` (one file, one annotation set) and `Video` (one file,
annotations on lazily-created `VideoFrame` rows). Bio-imaging and industrial inspection users work with **OME-TIFF**:
a multi-dimensional XYCZT container with an embedded OME-XML description, optional multi-resolution pyramid, optional
BigTIFF (>4 GB) encoding, and optional multi-file (companion) layout.

We want to support OME-TIFF end to end - upload, annotate, train, quantize, predict, export - and we want the same
design to absorb **OME-Zarr (NGFF)** later without a schema migration or an API break. OME-Zarr shares the OME data
model but is a chunked directory store that is routinely read remotely from object storage, so it is the forcing
function for cloud scalability.

### Requirements addressed

1. Upload OME-TIFF (single- and multi-file, classic and BigTIFF) within configured upload/storage limits.
2. Parse OME-XML and use it to interpret dimensions and organization. X, Y and C are mandatory; Z and T optional;
   other axes ignored.
3. Navigate XYCZT in the annotator: Z as a slider, T as a timeline, C as configurable per-channel color + display
   window, pyramid used for efficient zoom.
4. Annotate labels/boxes/polygons on individual XYC frames (i.e. per `(Z, T)`).
5. Train all available models on datasets containing annotated OME-TIFF images.
6. Quantize trained models.
7. Predict on other OME-TIFF images.
8. Export models for inference outside Geti.

---

## 2. Decision drivers

- **Reuse the video-frame mechanism.** `MediaDB` already models a container plus lazily-created leaf rows
  (`video_id` + `frame_index`, with `UniqueConstraint("video_id", "frame_index")`), and `DatasetItemDB.id` is an FK to
  `media.id`. Annotations, views, revisions, training, evaluation and export all hang off that. Anything that fits this
  shape is free downstream.
- **No breaking API changes.** The UI contract must stay stable; everything is additive.
- **Cloud-ready, not cloud-now.** Do not build remote storage today. Do isolate every assumption that would block it
  behind one abstraction.
- **No library changes.** `getitune` must not learn about OME.

### Rejected alternatives

| Alternative                                            | Why rejected                                                                                                                                                                     |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| New `ome_media` table parallel to `media`              | Forks every downstream query (`dataset_items`, `dataset_views`, revision export). The whole value of the design is that OME planes _are_ media.                                  |
| Client-side decoding (extend the existing `UTIF` path) | Cannot handle BigTIFF or pyramids; cannot read Zarr at all; and the window/level maths must match training preprocessing exactly, which requires one server-side implementation. |
| Teach `getitune` to read OME                           | Large, couples library to application concerns, violates "do not import from `application/`" in spirit. Backend materializes plain PNGs instead.                                 |

---

## 3. Decision

### 3.1 Domain model

| OME concept                                 | Geti entity                                                                                   |
| ------------------------------------------- | --------------------------------------------------------------------------------------------- |
| An uploaded OME-TIFF / OME-Zarr image       | `OmeImage` - one `MediaDB` row, `type = "ome_image"`                                          |
| An annotatable `(Z, T)` plane, all channels | `OmePlane` - one `MediaDB` row, `type = "ome_plane"`, created lazily on first annotation      |
| X, Y                                        | `media.width` / `media.height` (full-resolution level)                                        |
| C                                           | Not a media row. A rendering concern (`OmeChannelView`) and a training-preprocessing concern. |
| Z, T                                        | `ome_plane.z_index` / `t_index`, plus a linear `frame_index`                                  |
| Pyramid levels                              | Metadata only (`ome_images.pyramid_levels`), never media rows                                 |
| Other axes                                  | Ignored; series 0, index 0 assumed                                                            |

`OmePlane` is to `OmeImage` what `VideoFrame` is to `Video`. Because it is a `MediaDB` row, it automatically
participates in `dataset_items`, `dataset_items_labels`, `dataset_view_items`, dataset revisions, training, evaluation
and prediction with **no changes to those tables**.

### 3.2 New entities

```
OmeImage        - media row (container), type="ome_image"
OmePlane        - media row (leaf),      type="ome_plane", parent_id -> OmeImage
OmeImageInfo    - 1:1 with OmeImage; OME-XML-derived structure (new table)
OmeChannelView  - 1:1 with OmeImage; user display settings (new table)
MediaStorage    - value object, not persisted; abstracts "where the bytes are"
OmeReader       - service protocol, one implementation per container format
```

### 3.3 Storage abstraction (the cloud-scalability hinge)

`MediaService.get_media_binary_path()` returns a `Path` to a single movable file. That assumption breaks for multi-file
OME-TIFF _today_ and for Zarr _tomorrow_. Replace it (additively - keep the old method for images/videos) with:

```python
@dataclass(frozen=True)
class MediaStorage:
    """Where a media's bytes live. A single file, a directory of files, or (later) a remote store."""

    root: Path                 # later: a URI + an fsspec-style filesystem
    entrypoint: Path | None    # companion .ome / .zattrs; None for single-file media
    is_directory: bool
```

Everything that reads, sizes, moves or deletes media bytes goes through this. The remote case is then a change to one
dataclass and its factory, not to twenty call sites.

### 3.4 Reader abstraction

```python
class OmeReader(Protocol):
    """One implementation per container format: OmeTiffReader now, OmeZarrReader later."""

    def parse(self, storage: MediaStorage) -> OmeImageInfo: ...
    def read_plane(
        self, storage: MediaStorage, z: int, t: int, channels: list[int], level: int
    ) -> np.ndarray: ...
    def read_tile(
        self, storage: MediaStorage, z: int, t: int, level: int, x: int, y: int
    ) -> np.ndarray: ...
```

`OmeTiffReader` is backed by `tifffile` (the only library that handles OME-XML, pyramids and BigTIFF). Reader selection
is on `media.format`. Windowing, RGB mapping, caching, thumbnailing and training-set materialization all live _above_
this protocol and are written once.

### 3.5 Rendering

Rendering is **server-side**. A plane is rendered by:

1. Choosing a pyramid level from the requested output size.
2. Reading the enabled channels at that level.
3. Applying per-channel window/level: `v <= min -> 0`, `v >= max -> 255`, linear between.
4. Compositing enabled channels into their assigned RGB targets.

The result is cached on disk as `projects/{pid}/dataset/{media_id}-r{level}-z{z}-t{t}-{settings_hash}.png`, invalidated
by the settings hash. Caching by hash (not by timestamp) means the cache is correct across settings changes and is
trivially movable to object storage later.

### 3.6 Training

A dataset revision materializes **annotated planes only**, rendered to plain PNG into `dataset_revisions/<id>/images/`,
using the channel view settings in force at revision time. Those settings are recorded in the revision so it stays
reproducible and so inference-time preprocessing can be made to match training-time preprocessing.

This is exactly how annotated video frames are already handled, which is why requirements 5–8 need no work in `getitune`.

---

## 4. Schema changes

### 4.1 `MediaDB` - generalize the parent/leaf columns

```python
class MediaDB(BaseID):
    __tablename__ = "media"
    __table_args__ = (
        Index("idx_media_parent_id", "parent_id"),
        UniqueConstraint("parent_id", "frame_index", name="uq_parent_id_frame_index"),
    )
    ...
    # Renamed from video_id. Parent container: a Video for video frames, an OmeImage for OME planes.
    parent_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("media.id", ondelete="CASCADE"), nullable=True, default=None
    )
    # Linear index within the parent: video frame number, or (z + t * size_z) for OME planes.
    frame_index: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    # Populated only for ome_plane rows. Redundant with frame_index, but needed for filtering/sorting.
    z_index: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    t_index: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)

    # Widened: BigTIFF and Zarr stores exceed 2^31 bytes.
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
```

`DatasetRevisionDB.size` is widened to `BigInteger` for the same reason.

The `video_id` → `parent_id` rename is the only invasive change. It is a pure DDL rename with no data migration, and it
prevents a second self-FK column being added for every future container type.

### 4.2 `OmeImageDB` - new table, 1:1 with an `ome_image` media row

```python
class OmeImageDB(Base):
    """OME-XML/NGFF-derived structure of an uploaded OME image."""

    __tablename__ = "ome_images"

    media_id: Mapped[str] = mapped_column(
        Text, ForeignKey("media.id", ondelete="CASCADE"), primary_key=True
    )
    container_format: Mapped[str] = mapped_column(String(20), nullable=False)  # ome_tiff | ome_zarr
    size_x: Mapped[int] = mapped_column(Integer, nullable=False)
    size_y: Mapped[int] = mapped_column(Integer, nullable=False)
    size_z: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    size_c: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    size_t: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Free-form axis string, e.g. "XYCZT". NGFF declares axis order per image, so this is
    # deliberately not constrained to the OME-TIFF permutations.
    dimension_order: Mapped[str] = mapped_column(String(16), nullable=False)
    pixel_type: Mapped[str] = mapped_column(String(20), nullable=False)
    series_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_big_tiff: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # [{"index": 0, "name": "DAPI", "color": "#0000ff", "emission_wavelength": 461}, ...]
    channels: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # [{"level": 0, "width": 40000, "height": 30000, "scale": [1,1,1,1,1]}, ...]; empty if not pyramidal
    pyramid_levels: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Multi-file layouts: entrypoint + constituent files, relative to the media root.
    entrypoint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    files: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Verbatim OME-XML / NGFF attributes, for provenance and re-parsing without touching bytes.
    raw_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)
```

JSON columns for `channels` / `pyramid_levels` / `files` are consistent with the existing treatment of `config_data`,
`training_configuration` and `label_schema_revision`: read as a whole, never queried into. Including `scale` per
pyramid level and leaving `dimension_order` free-form is what lets OME-Zarr land without a migration.

### 4.3 `OmeChannelViewDB` - new table, user display state

```python
class OmeChannelViewDB(Base):
    """Per-image channel-to-RGB mapping and display windows used by the annotator and by
    training-set materialization."""

    __tablename__ = "ome_channel_views"

    media_id: Mapped[str] = mapped_column(
        Text, ForeignKey("media.id", ondelete="CASCADE"), primary_key=True
    )
    # [{"channel": 2, "target": "red", "enabled": true, "window_min": 120, "window_max": 4000}, ...]
    settings: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
```

Kept separate from `ome_images` so resetting the view never rewrites structural metadata. An absent row means
"server-computed default": first one or three channels, auto-contrast from a percentile sample. This shape maps 1:1 onto
NGFF `omero.channels[].window` + `.color`, so OME-Zarr reuses it as-is.

### 4.4 Unchanged

`dataset_items`, `dataset_items_labels`, `dataset_views`, `dataset_view_items`, `dataset_revisions`, `model_revisions`,
`model_variants`, `evaluations`, `metric_scores`, `uploads`. This is the measure of whether the design is right.

### 4.5 Migration

One Alembic revision:

1. `media.video_id` → `media.parent_id`; rename `idx_media_video_id` and `uq_video_id_frame_index`.
2. Add `media.z_index`, `media.t_index`.
3. Widen `media.size` and `dataset_revisions.size` to `BigInteger`.
4. Create `ome_images`, `ome_channel_views`.

SQLite requires `op.batch_alter_table` for (1) and (3); follow the existing pattern in `app/alembic/versions/`.
Downgrade is symmetric and lossless as long as no OME media exists; the downgrade must therefore refuse to run if any
`ome_image` row is present.

---

## 5. API contract

All additive, under the existing `/api/projects/{project_id}/media` router.

### 5.1 Upload

Single-file OME-TIFF needs no new endpoint - the existing `POST /media` and `POST /media:from-upload` work once format
parsing handles compound extensions (`.ome.tiff`). For multi-file layouts:

```http
POST /api/projects/{project_id}/media:from-upload
Content-Type: application/json

{ "upload_id": "0c2f…", "name": "plate_A01" }

Accepted uploads now additionally include:
  *.ome.tiff / *.ome.tif   single-file OME-TIFF (classic or BigTIFF)
  *.ome.zip                zipped multi-file OME-TIFF companion set
  *.zarr.zip               zipped OME-Zarr store (future)

201 Created -> MediaView
413 -> exceeds configured upload or storage limit
422 -> unsupported extension, malformed archive, or invalid/unreadable OME metadata
```

`source` is a **discriminated object, not a bare array**, so the future variants `{"kind": "archive", "upload_id": "…"}`
(a zipped Zarr store) and `{"kind": "remote", "url": "s3://…"}` are additive rather than breaking. This is a free
decision today and an API break if skipped.

### 5.2 Structure

```http
GET /api/projects/{project_id}/media/{media_id}/ome

200 ->
{
  "container_format": "ome_tiff",
  "size_x": 40000, "size_y": 30000, "size_z": 60, "size_c": 5, "size_t": 1,
  "dimension_order": "XYCZT",
  "pixel_type": "uint16",
  "is_big_tiff": true,
  "channels": [{"index": 0, "name": "DAPI", "color": "#0000ff"}, …],
  "pyramid_levels": [{"level": 0, "width": 40000, "height": 30000, "scale": [1,1,1,1,1]}, …]
}
404 -> media is not an OME image
```

### 5.3 Channel view

```http
GET /api/projects/{project_id}/media/{media_id}/channel-view
200 -> {"settings": [ … ], "is_default": true}

PUT /api/projects/{project_id}/media/{media_id}/channel-view
{"settings": [{"channel": 2, "target": "red", "enabled": true,
               "window_min": 120, "window_max": 4000}, …]}
200 -> {"settings": [ … ], "is_default": false}
422 -> channel index out of range, window_min >= window_max, duplicate RGB target
```

### 5.4 Rendering

```http
GET /api/projects/{project_id}/media/{media_id}/render?z=12&t=0&level=2
200 -> image/png, Cache-Control: private, max-age=…, ETag: {settings_hash}
```

Window/level is deliberately **not** in the query string: the render reflects the stored channel view, so responses are
cacheable and identical to what training will see. `PUT /channel-view` invalidates via the `ETag`.

Optional, added only if profiling demands it (and the natural fit for Zarr chunks):

```http
GET /api/projects/{project_id}/media/{media_id}/tiles/{level}/{x}/{y}?z=12&t=0
200 -> image/png
```

### 5.5 Plane listing and thumbnails

Mirrors the existing `list_video_frames`:

```http
GET /api/projects/{project_id}/media/{media_id}/planes?z=&t=&limit=&offset=
200 -> paginated OmePlane views (annotated planes only), for Z-slider / T-timeline overlays

GET /api/projects/{project_id}/media/{media_id}/thumbnail?z=12&t=0
200 -> image/jpeg
```

### 5.6 Annotations - no new endpoints

Extend the `_get_request_media` dependency so that, alongside `frame_index`, it accepts `z` and `t`. When the addressed
media is an `ome_image`, it resolves - or lazily creates - the corresponding `ome_plane` row, exactly as the video-frame
branch does today. The existing annotation `GET`/`PUT` then work verbatim:

```http
GET /api/projects/{project_id}/media/{media_id}/annotations?z=12&t=0
PUT /api/projects/{project_id}/media/{media_id}/annotations?z=12&t=0
400 -> z or t out of range for this image
```

### 5.7 Prediction

Generalize the range object additively; `range` keeps working for videos.

```python
class PlaneRange(BaseModel):
    z: VideoRange | None  # start/end/stride over Z
    t: VideoRange | None  # start/end/stride over T


class MediaPredictionRequest(BaseModel):
    media_id: UUID
    range: VideoRange | None = None       # videos (unchanged)
    plane_range: PlaneRange | None = None  # OME images (new)
```

### 5.8 Response models

`OmeImage` and `OmePlane` are added to the `Media` discriminated union keyed on `type`. Additive to the OpenAPI spec;
regenerate with `just gen-api-spec` then `npm run build:api`.

---

## 6. Library impact

**None.** Because the backend materializes annotated planes as ordinary PNGs into the dataset revision, training,
quantization, evaluation and model export are unchanged, and exported models consume plain RGB outside Geti -
satisfying requirements 5 through 8.

The only reason to touch `libraries/getitune/` would be true N-channel training (feeding all `size_c` channels instead
of an RGB projection). That requires per-recipe input-conv changes and pretrained-weight adaptation, with real accuracy
questions. It is explicitly **out of scope** here and should be a separate proposal.

One item to verify: whether the library's preprocessing accepts 16-bit PNG, in case we later want to materialize at
native bit depth. If not, 8-bit after windowing is the answer, which is what this design does anyway.

---

## 7. Cloud scalability

What this design **enables without further schema or API change**:

- OME-Zarr: a new `OmeZarrReader` plus `container_format = "ome_zarr"`. The data model, all five new/changed tables,
  and every endpoint in §5 are reused verbatim.
- Remote stores: `MediaStorage` grows a URI + filesystem; `ome_images.files` already holds opaque strings. Training-set
  materialization becomes the pull-local boundary.
- Object-storage render cache: the cache key is a content hash, not a timestamp or a local path.
- Tile-based streaming: §5.4 already specifies the endpoint shape.

What is **deliberately deferred**:

- Actual remote/lazy reading. No requirement today; building it now means an `fsspec` dependency and a much larger test
  surface.
- Chunk-level caching and prefetching.
- Distributed rendering. Rendering is CPU-bound and cacheable; the existing background-task mechanism is sufficient
  until measured otherwise.

What would **block** cloud scaling if we did not do it now, and therefore is in scope: the `MediaStorage` abstraction,
the `OmeReader` protocol, the discriminated upload `source` body, and the `scale` field + free-form `dimension_order` in
the pyramid/axis metadata. All four are independently justified by the multi-file OME-TIFF requirement, so none is
speculative.

---

## 8. Implementation plan

Each step is independently mergeable and leaves `main` green.

### Step 1 - Schema and migration

Rename `video_id` → `parent_id`, add `z_index`/`t_index`, widen both `size` columns, create `ome_images` and
`ome_channel_views`. Update `MediaRepository`, `dataset_view_repo` and all `video_id` references. No behaviour change.

_Testing._ Alembic upgrade/downgrade test on a DB seeded with projects, videos and video frames, asserting row counts
and FK integrity are preserved. Run the existing video integration suite unchanged - it is the regression gate for the
rename. Add a `testcontainers` integration test asserting a `size` value above 2^31 round-trips.

### Step 2 - `MediaStorage` and `OmeReader` skeleton

Introduce `MediaStorage` and `MediaService.get_media_storage()`; make directory-backed media work for sizing, moving
and deletion. Define the `OmeReader` protocol with no implementations.

_Testing._ Unit tests for `MediaStorage` over single-file and directory layouts: recursive size, move,
discard-on-failure, delete. Assert existing image/video media still resolve to the identical paths.

### Step 3 - `OmeTiffReader`

`tifffile`-backed `parse` / `read_plane` / `read_tile`. Validate X/Y/C present, default Z/T to 1, ignore unknown axes,
select series 0.

_Testing._ `tests/unit/services/ome/test_ome_tiff_reader.py` against small fixtures committed under `tests/assets/`:
XYC only, XYCZ, XYCZT, pyramidal, BigTIFF (a minimal one), and a non-OME TIFF that must be rejected cleanly.
Parametrize plane selection over `(z, t)` and assert shape, dtype and a known pixel value. Malformed OME-XML must raise
`InvalidImageError`, not propagate a `tifffile` exception.

### Step 4 - Ingest

`ImageFormat` gains `ome.tiff`/`ome.tif`; replace the `ImageFormat[ext.upper()]` lookup with a longest-suffix value
match in `_parse_media_format` **and** in `dataset_revision_service._parse_revision_item_from_df_row_dict`, which will
otherwise raise on compound suffixes. Add `MediaService.create_ome_image()`, the `:from-uploads` endpoint, and the `/ome`
endpoint. Thumbnail from the lowest pyramid level at mid-Z/mid-T, mirroring `create_video`.

_Testing._ Router unit tests for compound-extension parsing, including that `a.ome.tiff` resolves to `OME_TIFF` and
`b.tiff` still resolves to `TIFF`. Integration tests for upload of each fixture asserting the `MediaDB` + `OmeImageDB`
rows, the thumbnail file, and that a failed parse leaves no orphaned bytes on disk. Negative tests for limit violations
(413) and malformed metadata (422).

### Step 5 - Rendering and channel view

Default-settings computation, window/level compositing, the `/channel-view` endpoints, `/render`, and the hash-keyed
disk cache.

_Testing._ Unit tests for the window/level transform (boundary values at `min`, `max`, midpoint; clipping; a disabled
channel contributing zero). Golden-image test for a known fixture + known settings. Cache tests: identical request is
a cache hit; `PUT /channel-view` invalidates; concurrent renders of the same key do not corrupt the file.
Validation tests for the 422 cases in §5.3.

### Step 6 - Annotation

`MediaType.OME_IMAGE` / `OME_PLANE`, Pydantic `OmeImage` / `OmePlane`, lazy `create_ome_plane`, `z`/`t` in
`_get_request_media`, `/planes` and plane `/thumbnail`. Audit every `MediaType.VIDEO_FRAME` filter -
`dataset_view_repo` (×4), `dataset_view_service`, `demo_files_service` - and replace them with a shared
`LEAF_MEDIA_TYPES` constant so the next container type cannot be forgotten.

_Testing._ Integration test: annotate `(z=12, t=0)`, assert exactly one `ome_plane` row plus one `dataset_item`;
re-annotate and assert no duplicate row (this is what `uq_parent_id_frame_index` guards). Out-of-range `z`/`t`
returns 400. Media listing and counting must exclude `ome_plane` rows exactly as they exclude `video_frame`. Deleting
the parent returns 401. cascades to planes, items and labels.

### Step 7 - Training

Materialize annotated planes into the revision `images/` directory using the stored channel view; record the settings
in the revision.

_Testing._ Integration test building a revision from a project containing an OME image with three annotated planes,
asserting the rendered PNG count, the parquet rows and the subset counts. BDD scenario (`behave`) covering
upload → annotate → train → quantize → export on a small fixture, which is the single end-to-end gate for requirements 5–8.

### Step 8 - Prediction

`PlaneRange`, `MediaService.get_plane_binaries()`, `MediaNumpyLoader` dispatch on `media.type`, SAM loader dispatch.

_Testing._ Unit test that `load_media_binary` for an `ome_plane` returns the same `(H, W, C)` RGB(A) contract as for a
JPEG. Integration test predicting over a `PlaneRange` with a stride, asserting the predicted plane set. Assert the
existing video `range` behaviour is byte-identical (regression gate for the additive change).

### Step 9 - Contract handoff

`just gen-api-spec`, copy to `application/ui/src/api/openapi-spec.json`, `npm run build:api`, add mock handlers for the
new endpoints, update [`dataset.md`](../dataset.md) and [`entities.md`](../entities.md).

_Testing._ `just lint`, `just pyrefly`, `just lint-imports` on the backend; `npm run type-check` on the UI to prove the
regenerated types compile.

### Step 10 (future) - OME-Zarr

Add `OmeZarrReader`, `container_format = "ome_zarr"`, and the `archive` / `remote` upload source kinds. No schema
migration, no API break.

---

## 9. Risks

| Risk                                                 | Mitigation                                                                                                                                                                 |
| ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| New `tifffile` dependency                            | Verify licence and that it reaches `geti.spec` `hiddenimports`; PyInstaller smoke test in step 3.                                                                          |
| `video_id` → `parent_id` rename churn                | Mechanical; step 1 is isolated and gated by the existing video suite. If rejected, keep the name and document it as "parent media" - the rest of the design is unaffected. |
| Render latency makes Z/T scrubbing unusable          | Measure at step 5 on a pyramidal BigTIFF fixture. If it fails, promote `/tiles` from optional to required; the endpoint shape is already specified.                        |
| Large stores blow past disk limits                   | Enforce limits in `create_ome_image` through the settings layer, never ad hoc; cover with the 413 test in step 4.                                                          |
| RGB projection loses information needed for accuracy | Accepted for v1 and consistent with the requirements. Record the projection in the revision so N-channel training can later be compared against it fairly.                 |
| Downgrade path with OME media present                | Downgrade refuses to run if any `ome_image` row exists; documented in [`migration-guidelines.md`](../migration-guidelines.md).                                             |

---

## 10. Out of scope

- N-channel (C > 3) model input in `getitune`.
- Remote/lazy store reading and chunk-level caching.
- Multiple OME series per file (series 0 only).
- Non-XYCZT axes.
- UI implementation (separate workstream; this document fixes the contract it consumes).
