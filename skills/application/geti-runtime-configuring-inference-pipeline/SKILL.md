---
name: geti-runtime-configuring-inference-pipeline
description: Configure and validate the Geti runtime inference pipeline in application mode. Use when a user needs to set up or troubleshoot source → model → sink configuration, tune pipeline parameters, diagnose bad predictions or throughput issues, verify deployment settings, or move a project from trained model to stable runtime inference without changing backend implementation code.
---

# Geti Runtime: Configuring Inference Pipeline

Use this skill to operate the Geti application pipeline as a runtime workflow.
This skill is for configuration and validation, not backend code development.

## When to Use

- User asks how to configure source, model, and sink for live inference.
- User reports pipeline issues such as no frames, no predictions, or unstable throughput.
- User wants a safe checklist to move from trained model to enabled runtime pipeline.
- User needs to validate that pipeline configuration changes are effective.

## Scope

- In scope: runtime API usage, pipeline configuration, status checks, and operational diagnostics.
- Out of scope: implementing new backend endpoints or changing backend internals.

## Procedure

1. Confirm prerequisites.
   - Get backend endpoint and auth details if needed.
   - Confirm project exists and a trained model is available.
   - Confirm source and sink endpoints are reachable.
2. Collect the current state first.
   - Read project state and current pipeline configuration.
   - Capture source, selected model, sink, and pipeline status before editing.
   - Avoid blind overwrite when partial updates are enough.
3. Configure the project pipeline.
   - Model: Verify the source format is compatible with the selected model (8b vs 16b).
   - Source: Verify connectivity.
   - Sink: Verify destination connectivity and configured formats.
4. Enable the pipeline.
   - Activate the pipeline only after all three components are fully validated.
   - Prefer a minimal-change rollout to isolate failures.
5. Validate end-to-end.
   - Verify that frames are successfully ingested from the source and rendered with predicted labels.
   - Confirm that inference output is delivered to your configured sink in the expected format.
