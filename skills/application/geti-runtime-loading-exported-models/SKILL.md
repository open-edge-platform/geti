---
name: geti-runtime-loading-exported-models
description: Load and validate exported models for Geti runtime inference. Use when a user needs to import OpenVINO or ONNX artifacts into the Geti application pipeline, verify model metadata compatibility with project task and labels, diagnose model load failures, or confirm export-to-runtime handoff from getitune training.
---

# Geti Runtime: Loading Exported Models

Use this skill to bridge model export outputs and runtime deployment in Geti.
This skill focuses on import and compatibility validation, not model retraining.

## When to Use

- User has exported model artifacts and needs to run them in Geti runtime.
- Model import succeeds partially but runtime inference fails.
- User asks how to validate model package compatibility before enabling pipeline.
- User needs a repeatable checklist for export-to-runtime handoff.

## Scope

- In scope: model artifact checks, runtime loading workflow, metadata validation, load diagnostics.
- Out of scope: changing training code, model architecture, or backend feature implementation.

## Procedure

1. Verify artifact completeness.
   - Confirm expected files for the chosen export format are present.
   - Confirm files are readable and not truncated.
   - Confirm the export target format matches runtime expectations.
2. Verify metadata compatibility.
   - Confirm task type compatibility with the destination project.
   - Confirm label set alignment between model and project configuration.
   - Confirm input expectations (shape, color space, preprocessing assumptions).
3. Import model into runtime.
   - Register or upload model package through the runtime workflow.
   - Record model identifier and version used for deployment.
4. Bind model to pipeline.
   - Attach imported model to target pipeline configuration.
   - Ensure confidence and postprocessing defaults are sane for the task.
5. Run smoke validation.
   - Execute quick inference on known sample inputs.
   - Verify output classes and score ranges are plausible.
   - Verify no runtime loader errors remain.
