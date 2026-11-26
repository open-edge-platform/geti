# Integration Tests

## Scope

Integration tests in this directory validate end-to-end model loading and inference through Model API wrappers.
Result is not compared against reference outputs, but rather we check that the model can be loaded and run without exceptions on a sample, random input.

Current coverage is centered on `tests/integration/test_model.py`, which:

- Resolves model targets from CLI options (`--model-path` or HF Hub `--author`/`--collection`)
- Loads models via:
  - `Model.create_model(...)` for local paths
  - `Model.from_pretrained(...)` for `hf://...` references
- Runs inference on a deterministic random RGB image (`640x640x3`, `uint8`)
- Passes if no exception is raised during load + single inference call

In short, this is a smoke/integration check for model usability, not an accuracy benchmark.

## Inputs and Parametrization

`pytest_generate_tests` in `tests/integration/test_model.py` dynamically parametrizes `path`:

1. If `--model-path` is provided:
   - `hf://...` => treated as a single HF model
   - file path => single local model
   - directory => recursively collects all `*.xml` files
2. Else, if `--author` is set:
   - fetches model repos from HF Hub
   - optionally filtered by `--collection`
3. If no paths are resolved:
   - test is skipped

## CLI Options

Defined in `tests/integration/conftest.py`:

- `--model-path` (default: `None`)
  Local file, local directory, or `hf://repo_id`
- `--device` (default: `AUTO`)
  Target inference device, e.g. `CPU`, `GPU`, `AUTO`
- `--author` (default: `OpenVINO`)
  HF Hub author/organization used when `--model-path` is not passed
- `--collection` (default: `vision`)
  HF Hub collection under `author`

> Note: because `author`/`collection` have defaults, running this test without args attempts HF Hub discovery [OpenVINO/vision](https://huggingface.co/collections/OpenVINO/vision) unless you explicitly pass `--model-path`.

## Usage

Run from the `model_api` repository root.

### Default usage

When executed without any CLI options, the test will attempt to discover models from HF Hub [OpenVINO/vision](https://huggingface.co/collections/OpenVINO/vision) collection and run inference on all of those.

```bash
uv --directory model_api run pytest tests/integration/test_model.py
```

### All models from HF Hub author

```bash
uv --directory model_api run pytest tests/integration/test_model.py --author hf_author_name
```

### All models from HF Hub author and collection

```bash
uv --directory model_api run pytest tests/integration/test_model.py --author hf_author_name --collection collection_name
```

### Single model from HF Hub

```bash
uv --directory model_api run pytest tests/integration/test_model.py --model-path hf://OpenVINO/resnet50-int8-ov
```

### Single local model with absolute path

```bash
uv --directory model_api run pytest tests/integration/test_model.py --model-path /absolute/path/to/model.xml
```

### Single local model with path relative to `model_api` package root

```bash
uv --directory model_api run pytest tests/integration --model-path data/anomalib_models/padim.xml
```

### Multiple local models from a directory

```bash
uv --directory model_api run pytest tests/integration --model-path data/anomalib_models
```
