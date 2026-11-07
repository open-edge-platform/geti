# OME-\* Format Support (OME-TIFF now, OME-Zarr later)

- Scope: `application/backend/` (primary), `application/ui/` (separate workstream), `libraries/getitune/` (no change)
- Supersedes: nothing
- Related docs: [`entities.md`](entities.md), [`dataset.md`](dataset.md), [`migration-guidelines.md`](migration-guidelines.md)

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
Region          - value object; a pixel rectangle in coordinates of a pyramid level
OmeReader       - format-specific opener/prober; one implementation per container format
OmeImageHandle  - scoped, open-image interface for metadata and pixel-region reads; not persisted
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

    @property
    def is_directory(self) -> bool:
        return self.entrypoint is not None
```

Everything that reads, sizes, moves or deletes media bytes goes through this. The remote case is then a change to one
dataclass and its factory, not to twenty call sites.

### 3.4 Reader abstraction

```python
class OmeImageHandle(Protocol):
    """An open image. Metadata is parsed once; reads are lazy."""

    info: OmeImageInfo

    def read_region(
        self,
        *,
        level: int = 0,
        region: Region | None = None,  # None means the full image at this level
        z: int = 0,
        t: int = 0,
        channels: Sequence[int] | None = None,  # None means all channels
    ) -> np.ndarray: ...

    def close(self) -> None: ...
    def __enter__(self) -> "OmeImageHandle": ...
    def __exit__(self, *exc) -> None: ...


class OmeReader(Protocol):
    """One implementation per container format: OmeTiffReader now, OmeZarrReader later."""

    def probe(self, storage: MediaStorage) -> bool: ...
    def open(self, storage: MediaStorage, series: int = 0) -> OmeImageHandle: ...
```

The handle is the core pixel-access abstraction: it returns a `(C, H, W)` array in the requested channel order and
normalizes on-disk axis order. A full plane is `read_region(region=None, z=..., t=...)`; a crop is a `Region` at the
requested pyramid level. Regions use level-local pixel coordinates; implementations may use native tiles/chunks
internally. The API exposes full-plane rendering in v1; if partial rendering is later needed, it should extend the
existing render endpoint. Handles own any open file/store resources and must be closed (preferably with a context
manager).

The reader only identifies and opens a format. `open()` parses metadata once and exposes it as `handle.info`; ingest
persists that metadata before closing the handle. Reader selection uses `probe(storage)` rather than trusting
`media.format`, which may only describe the filename extension. `OmeTiffReader` is backed by `tifffile` (with lazy
region reads); an OME-Zarr reader can implement the same handle contract later. Windowing, RGB mapping, caching,
thumbnailing and training-set materialization all live _above_ this protocol and are written once.

### 3.5 Rendering

Rendering is **server-side**. A plane is rendered by:

1. Resolving the requested pyramid `level` (an explicit query parameter, §5.4) against `ome_images.pyramid_levels`.
2. Reading the enabled channels at that level.
3. Applying per-channel window/level: `v <= min -> 0`, `v >= max -> 255`, linear between.
4. Compositing enabled channels into their assigned RGB targets.

### 3.6 Training

Training uses a **fixed, deterministic channel-to-RGB mapping** computed once from immutable OME metadata
(§3.6.1), independent of anything the annotator UI does.

A dataset revision materializes **annotated planes only**, rendered to plain PNG into `dataset_revisions/<id>/images/`,
using that fixed mapping. The mapping actually used is written alongside the revision as a sidecar file,
`dataset_revisions/<id>/ome_channel_mapping.json` - the revision's on-disk artifacts are the documented source of
truth for "what did training see", exactly as the rendered PNGs themselves already are. This avoids adding a
revision-scoped settings table or JSON column (§4.4 stays correct: `dataset_revisions` is unchanged), while still
making the preprocessing fully reproducible from what is stored for that revision.

This is exactly how annotated video frames are already handled, which is why requirements 5–8 need no work in `getitune`.

#### 3.6.1 Fixed training channel mapping

Computed once, at ingest time, from `handle.info` (`OmeTiffReader.open` parses the OME metadata), `size_c` and the
channel metadata, and stored immutably on `OmeImageDB.channel_mapping` (§4.2) - **not** the `OmeChannelView` row, which
only affects rendering for the annotator and can change at any time. Because it's derived solely from already-immutable
OME metadata and persisted once, it's as reproducible as the pixel data itself.

Strategy, in priority order:

1. **`size_c == 3` and no better signal available**: identity mapping, channel `i` → RGB target `i`. Covers the common
   "already RGB" OME-TIFF case.
2. **OME-XML declares `EmissionWavelength` for each channel**: map each channel to the nearest of {red, green, blue} by
   wavelength (e.g. `<500nm` → blue, `500-580nm` → green, `>580nm` → red), picking at most one channel per target and
   preferring the one whose declared `Color` is closest to the target hue if more than one collides. Covers
   fluorescence imaging, the primary OME-TIFF use case and the one place a naive first-three-channels choice would be
   actively wrong (e.g. DAPI/GFP/Cy5 in channel order 0,1,2 vs. 2,0,1).
3. **Fallback, any `size_c` with no wavelength metadata**: first `min(size_c, 3)` channels, in index order, mapped to
   R, G, B; channels beyond index 2 are dropped. `size_c < 3` pads unused targets with zero (black).

The mapping is recorded as `[{"channel": 2, "target": "red"}, …]` - the same shape as `OmeChannelView.settings` minus
the window/level fields, since training always uses the channel's full declared range rather than a user-tuned
window. Re-ingesting an image recomputes it the same way, so refining the strategy later never needs a migration of
its own - only newly-ingested images pick up the change, and each image's revision sidecar still truthfully records
whichever mapping was used for it.

Proposed file structure:

```
// dataset_revisions/<revision_id>/ome_channel_mappings.json
{
  "mapping_strategy_version": 1,          // bump if §3.6.1's algorithm changes; lets readers detect
                                           // "this revision predates strategy vN" without re-deriving it
  "images": [
    {
      "media_id": "3fae2b1e-....-ome_image_1",
      "container_format": "ome_tiff",
      "size_c": 3,
      "channel_mapping": [
        {"channel": 0, "target": "blue"},
        {"channel": 1, "target": "green"},
        {"channel": 2, "target": "red"}
      ]
    },
    {
      "media_id": "9b1caa02-....-ome_image_2",
      "container_format": "ome_zarr",
      "size_c": 5,
      "channel_mapping": [
        {"channel": 2, "target": "red"},
        {"channel": 0, "target": "green"},
        {"channel": 4, "target": "blue"}
      ]
    }
  ]
}
```

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
```

The `video_id` → `parent_id` rename is the only invasive change. It is a pure DDL rename with no data migration, and it
prevents a second self-FK column being added for every future container type.

**This rename is internal to the ORM/DB layer only.** The public `VideoFrame` (`app/models/media.py`) and
`VideoFrameView` (`app/api/schemas/media.py`) Pydantic models keep their existing `video_id: UUID` field name on the
wire - that is part of the stable API contract and must not change. The risk is not the wire schema, it's the
construction path: both models are currently built with
`VideoFrame.model_validate(db_media, from_attributes=True)`, which resolves `video_id` via
`getattr(db_media, "video_id")`. Once the ORM attribute becomes `parent_id`, that `getattr` silently breaks
(`AttributeError` / missing-field validation error) even though nothing about the public API changed.

Do **not** rely on `from_attributes` auto-mapping for this field after the rename. Instead:

- Construct `VideoFrame`/`VideoFrameView` explicitly for the `video_id` field (e.g.
  `VideoFrame.model_validate({**db_media.__dict__, "video_id": db_media.parent_id}, ...)`, or build the model via
  explicit kwargs), **or**
- Add a `model_validator(mode="before")` on `VideoFrame`/`VideoFrameView` that reads `.parent_id` off an ORM object and
  injects it as `video_id` before the rest of validation runs.

`OmePlane` is a new type with no legacy field name to preserve; decide its public field name (`parent_id` vs. a more
descriptive `ome_image_id`) once, since it becomes part of the stable contract from day one.

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
    # OME-XML format doesn't have a notion of window per channel like OME-Zarr, so window min/max is calculated from the
    # significant bits of the pixel type and stored in `channels[].window` for convenience.
    # [{"index": 0, "name": "DAPI", "color": "#0000ff", "emission_wavelength": 461,
    #   "window": { "min": 0, "max": 65535, "start": 0, "end": 40000 }
    #  }, ...]
    channels: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Fixed, deterministic channel->RGB projection used for training (see §3.6.1). Computed once at ingest
    # time and never mutated; independent of OmeChannelView, which is mutable and display-only.
    # [{"channel": 2, "target": "red"}, ...]
    channel_mapping: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
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
    """Per-image channel-to-RGB mapping and display windows used by the annotator."""

    __tablename__ = "ome_channel_views"

    media_id: Mapped[str] = mapped_column(
        Text, ForeignKey("media.id", ondelete="CASCADE"), primary_key=True
    )
    # [{"channel": 2, "color": "#3B6CFF", "enabled": true, "window_min": 120, "window_max": 4000}, ...]
    settings: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
```

Kept separate from `ome_images` so resetting the view never rewrites structural metadata. An absent row means
"server-computed default": first one or three channels, auto-contrast from a percentile sample. This shape maps 1:1 onto
NGFF `omero.channels[].window` + `.color`, so OME-Zarr reuses it as-is.

**Scope boundary:** this table is display-only (annotator rendering). Training never reads it - see §3.6/§3.6.1 for
the separate, immutable mapping used for revision materialization.

### 4.4 Unchanged

`dataset_items`, `dataset_items_labels`, `dataset_views`, `dataset_view_items`, `dataset_revisions`, `model_revisions`,
`model_variants`, `evaluations`, `metric_scores`, `uploads`. This is the measure of whether the design is right.

### 4.5 Migration

One Alembic revision:

1. `media.video_id` → `media.parent_id`; rename `idx_media_video_id` and `uq_video_id_frame_index`.
2. Add `media.z_index`, `media.t_index`.
3. Create `ome_images`, `ome_channel_views`.

SQLite requires `op.batch_alter_table` for (1); follow the existing pattern in `app/alembic/versions/`.
Downgrade is symmetric and lossless as long as no OME media exists; the downgrade must therefore refuse to run if any
`ome_image` row is present.

The rename in (1) is DB/ORM-internal only - see the callout in §4.1. Every `MediaDB.video_id` attribute reference must
become `MediaDB.parent_id` (repositories, filters, services), but the public `video_id` field on `VideoFrame` /
`VideoFrameView` must keep serializing under that name.

---

## 5. API contract

All additive, under the existing `/api/projects/{project_id}/dataset/media` router.

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
GET /api/projects/{project_id}/dataset/media/{media_id}/ome

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
400 -> media is not an OME image
404 -> media is not found
```

### 5.3 Channel view

```http
GET /api/projects/{project_id}/dataset/media/{media_id}/channel-view
200 -> {"settings": [ … ], "is_default": true}

PUT /api/projects/{project_id}/dataset/media/{media_id}/channel-view
{"settings": [{"channel": 2, "color": "#3B6CFF", "enabled": true,
               "window_min": 120, "window_max": 4000}, …]}
200 -> {"settings": [ … ], "is_default": false}
422 -> channel index out of range, window_min >= window_max, duplicate RGB target
```

### 5.4 Rendering

```http
GET /api/projects/{project_id}/dataset/media/{media_id}/render?z=12&t=0&level=2&c=0|120:2400$3B6CFF,1|300:9800$27C46A,2|40:1500$E8503A
200 -> image/png, ETag: {settings_hash}
     -> `c` omitted:  Cache-Control: private, no-cache
     -> `c` present:  Cache-Control: private, max-age=31536000, immutable
304 -> If-None-Match matched
400 -> malformed `c` (bad index, min >= max, invalid hex color)
422 -> level out of range for this image's pyramid_levels
```

**Query parameters**

| Param    | Required                              | Description                                    |
| -------- | ------------------------------------- | ---------------------------------------------- |
| `z`, `t` | no (default: stored defaults, else 0) | Plane and time point.                          |
| `level`  | no (default 0)                        | Pyramid level; 0 = full resolution.            |
| `c`      | no                                    | Per-request channel view override (see below). |

**Channel view resolution**

- **`c` omitted:** the render uses the stored channel view (`PUT .../channel-view`). The result is identical to what
  training will see.
- **`c` present:** the render uses the supplied view for this request only. Nothing is persisted. The UI uses this for
  live slider preview, and the same string can be placed in the app's URL to share a view.
- **Syntax:** `c=<index>|<min>:<max>$<RRGGBB>` entries, comma-separated.
  - A channel that is not listed is hidden.
  - Channels are composited additively and each is clamped to 0–255.
  - Intensity mapping: `value <= min → 0`, `value >= max → 255`, linear in between.
- **Optional fields:** `gamma`, `inverted` and the `rgb` slot mode are not in v1 of `c`. They can be added as extra
  `|`-separated fields without breaking existing clients.

**Caching**

- `ETag` is a hash of the _effective_ settings: `media_id`, `z`, `t`, `level`, and the channel view actually used
  (stored or override), plus the source version.
- Identical `c` values therefore hit the same cache entry. Clients should avoid sending sub-integer min/max values so
  the cache is reused.
- **`Cache-Control` differs by whether `c` is present:**
  - **`c` omitted** (stored, mutable channel view): `private, no-cache` - always revalidate via `ETag` before use, so
    a `PUT .../channel-view` is picked up on the very next load instead of being masked for up to `max-age`.
    Revalidation is cheap: an unchanged `ETag` just gets a `304`.
  - **`c` present** (fully specified in the URL): `private, max-age=31536000, immutable` - the URL can never resolve
    to different bytes, so it's safe to cache indefinitely and skip revalidation entirely (useful during slider
    scrubbing).
- A `PUT .../channel-view` only affects requests that omit `c`; their `ETag` changes automatically and is caught by
  the next revalidation.
- Server-side, decoded pixel data may be cached using format-native tiles/chunks as internal cache units. A new `c`
  then only reapplies the intensity mapping and color, with no storage read.

**Live preview (client guidance, non-normative)**

- While the user drags a slider, send `GET .../render?c=…` with no `PUT`. Throttle to one request per animation frame or
  about 50–100 ms.
- Optionally request one pyramid level lower during the drag and re-render at full quality on release.
- On commit (pointer release, about 500 ms idle, or an explicit save), send `PUT .../channel-view` in the background
  with optimistic UI. Rendering never waits on it.

**Deferred beyond v1:** If profiling or UI needs justify partial rendering or access to non-default series, extend
`/render` with optional `series` and level-local region parameters (`x`, `y`, `w`, `h`). Require all region
coordinates together, validate them against the selected series and pyramid level, and include the resolved series
and region in the ETag/cache key. Preserve the existing channel-view/compositing behavior.

### 5.5 Plane listing and thumbnails

Mirrors the existing `list_video_frames`:

```http
GET /api/projects/{project_id}/dataset/media/{media_id}/planes?z=&t=&limit=&offset=
200 -> paginated OmePlane views (annotated planes only), for Z-slider / T-timeline overlays

GET /api/projects/{project_id}/dataset/media/{media_id}/thumbnail?z=12&t=0
200 -> image/jpeg
```

### 5.6 Annotations - no new endpoints

Extend the `_get_request_media` dependency so that, alongside `frame_index`, it accepts `z` and `t`. When the addressed
media is an `ome_image`, it resolves - or lazily creates - the corresponding `ome_plane` row, exactly as the video-frame
branch does today. The existing annotation `GET`/`PUT` then work verbatim:

```http
GET  /api/projects/{project_id}/dataset/media/{media_id}/annotations?z=12&t=0
POST /api/projects/{project_id}/dataset/media/{media_id}/annotations?z=12&t=0
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
This includes the two `VideoFrame.model_validate(db_media, from_attributes=True)` call sites in
`media_service.py::save_video_frame` / `get_video_frame_by_video_id_and_index`, and the `MediaDB(video_id=...)`
constructor call - all must be updated to map `parent_id` to the public `video_id` field explicitly (see §4.1).

_Testing._ Alembic upgrade/downgrade test on a DB seeded with projects, videos and video frames, asserting row counts
and FK integrity are preserved. Run the existing video integration suite unchanged - it is the regression gate for the
rename. Add a `testcontainers` integration test asserting a `size` value above 2^31 round-trips. **Add a contract
regression test** that uploads a video, creates a video frame, and asserts the `GET .../media/{id}` response still
serializes `video_id` (not `parent_id`) with the correct value - this is the gate for the "no breaking API changes"
decision driver and would not be caught by the existing suite if it only checks ORM-level behaviour.

### Step 2 - `MediaStorage` and reader/handle skeleton

Introduce `MediaStorage` and `MediaService.get_media_storage()`; make directory-backed media work for sizing, moving
and deletion. Define the `OmeReader` and `OmeImageHandle` protocols and reader registry, with no format
implementations.

_Testing._ Unit tests for `MediaStorage` over single-file and directory layouts: recursive size, move,
discard-on-failure, delete. Assert existing image/video media still resolve to the identical paths.

### Step 3 - `OmeTiffReader`

Implement `probe` / `open` and the handle's `read_region` using `tifffile`. Validate X/Y/C present, default Z/T to 1,
ignore unknown axes, and use series 0 in v1. Region reads must support full planes and crops at any available pyramid
level without exposing format-specific tile/chunk mechanics.

_Testing._ `tests/unit/services/ome/test_ome_tiff_reader.py` against small fixtures committed under `tests/assets/`:
XYC only, XYCZ, XYCZT, pyramidal, BigTIFF (a minimal one), and a non-OME TIFF that must be rejected cleanly.
Parametrize region selection over `(z, t)`, channels and pyramid levels; assert the `(C, H, W)` shape, dtype and a
known pixel value. Verify handle context-manager cleanup. Malformed OME-XML must raise `InvalidImageError`, not
propagate a `tifffile` exception.

### Step 4 - Ingest

`ImageFormat` gains `ome.tiff`/`ome.tif`; replace the `ImageFormat[ext.upper()]` lookup with a longest-suffix value
match in `_parse_media_format` **and** in `dataset_revision_service._parse_revision_item_from_df_row_dict`, which will
otherwise raise on compound suffixes. Add `MediaService.create_ome_image()`, the `:from-upload` endpoint, and the `/ome`
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
the parent returns 204 - cascades to planes, items and labels.

### Step 7 - Training

Materialize annotated planes into the revision `images/` directory using the fixed channel mapping computed at
ingest time (§3.6.1); write `ome_channel_mapping.json` alongside the revision for provenance.

_Testing._ Integration test building a revision from a project containing an OME image with three annotated planes,
asserting the rendered PNG count, the parquet rows, the subset counts, and the sidecar mapping file content. Add a
unit test per mapping strategy in §3.6.1 (3-channel identity, wavelength-based, >3-channel fallback, <3-channel
padding). BDD scenario (`behave`) covering upload → annotate → train → quantize → export on a small fixture, which is
the single end-to-end gate for requirements 5–8.

### Step 8 - Prediction

`PlaneRange`, `MediaService.get_plane_binaries()`, `MediaNumpyLoader` dispatch on `media.type`, SAM loader dispatch.

_Testing._ Unit test that `load_media_binary` for an `ome_plane` returns the same `(H, W, C)` RGB(A) contract as for a
JPEG. Integration test predicting over a `PlaneRange` with a stride, asserting the predicted plane set. Assert the
existing video `range` behaviour is byte-identical (regression gate for the additive change).

### Step 9 - Contract handoff

`just gen-api-spec`, copy to `application/ui/src/api/openapi-spec.json`, `npm run build:api`, add mock handlers for the
new endpoints, update [`dataset.md`](dataset.md) and [`entities.md`](entities.md).

_Testing._ `just lint`, `just pyrefly`, `just lint-imports` on the backend; `npm run type-check` on the UI to prove the
regenerated types compile.

### Step 10 (future) - OME-Zarr

Add `OmeZarrReader`, `container_format = "ome_zarr"`, and the `archive` / `remote` upload source kinds. No schema
migration, no API break.

---

## 9. Risks

| Risk                                                                       | Mitigation                                                                                                                                                                                                                       |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| New `tifffile` dependency                                                  | Verify licence and that it reaches `geti.spec` `hiddenimports`; PyInstaller smoke test in step 3.                                                                                                                                |
| `video_id` → `parent_id` rename churn                                      | Mechanical; step 1 is isolated and gated by the existing video suite. If rejected, keep the name and document it as "parent media" - the rest of the design is unaffected.                                                       |
| `video_id` rename breaks public `VideoFrame`/`VideoFrameView` construction | `from_attributes=True` auto-mapping silently fails once the ORM attribute is `parent_id`; fix by mapping explicitly in `media_service.py` (see §4.1) and gate with the contract test added in step 1.                            |
| Render latency makes Z/T scrubbing unusable                                | Measure at step 5 on a pyramidal BigTIFF fixture. If partial rendering is needed, extend `/render` with region parameters.                                                                                                       |
| Large stores blow past disk limits                                         | Enforce limits in `create_ome_image` through the settings layer, never ad hoc; cover with the 413 test in step 4.                                                                                                                |
| RGB projection loses information needed for accuracy                       | Accepted for v1. The projection is a fixed, deterministic mapping (§3.6.1), decoupled from the mutable `OmeChannelView`, and recorded per-image and per-revision so it can be compared fairly against future N-channel training. |
| Downgrade path with OME media present                                      | Downgrade refuses to run if any `ome_image` row exists; documented in [`migration-guidelines.md`](migration-guidelines.md).                                                                                                      |

---

## 10. Out of scope

- N-channel (C > 3) model input in `getitune`.
- Remote/lazy store reading and chunk-level caching.
- Selecting a non-default OME series in v1; series 0 is used.
- Non-XYCZT axes.
- UI implementation (separate workstream; this document fixes the contract it consumes).
- Full-fidelity dataset export/import of OME media — export/import carries materialized PNGs and annotations only.
