---
name: geti-runtime-configuring-inference-pipeline
description: Configure and validate the Geti runtime inference pipeline in application mode. Use when a user needs to set up or troubleshoot source -> model -> sink configuration, tune pipeline parameters, diagnose bad predictions or throughput issues, verify deployment settings, or move a project from trained model to stable runtime inference without changing backend implementation code.
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
- Confirm project exists and a deployable model is available.
- Confirm source and sink endpoints are reachable.

2. Collect the current state first.
- Read project state and current pipeline configuration.
- Capture source, selected model, sink, and runtime toggles before editing.
- Avoid blind overwrite when partial updates are enough.

3. Configure in dependency order.
- Set source first and verify connectivity.
- Set model second and verify compatibility with task and labels.
- Set sink last and verify destination connectivity and format.

4. Enable or apply runtime mode.
- Activate the pipeline only after all three blocks validate.
- Prefer a minimal-change rollout to isolate failures.

5. Validate end to end.
- Verify frames are ingested from source.
- Verify inference output is produced for expected classes.
- Verify sink receives payloads or artifacts.
