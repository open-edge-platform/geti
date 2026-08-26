---
name: geti-runtime-running-live-inference
description: Run and operate live inference in the Geti application pipeline. Use when a user wants to start, monitor, stop, or recover source -> model -> sink runtime execution, verify production readiness, or troubleshoot live pipeline behavior such as stalls, dropped outputs, and latency regressions.
---

# Geti Runtime: Running Live Inference

Use this skill for operational control of live inference in Geti.
This skill is for runtime execution and monitoring, not code changes.

## When to Use

- User asks how to start or stop live inference for a configured pipeline.
- User needs runbook-style checks for runtime health and correctness.
- User reports stalls, dropped outputs, or latency spikes during live execution.
- User needs incident-style recovery steps with minimal disruption.

## Scope

- In scope: runtime start and stop flow, status monitoring, health verification, rollback and recovery.
- Out of scope: backend implementation changes and model retraining.

## Procedure

1. Pre-flight checks.
   - Confirm pipeline configuration is complete (source, model, sink).
   - Confirm model is loaded and selected.
   - Confirm endpoints for source and sink are reachable.
2. Start live inference.
   - Enable runtime execution through the application pipeline workflow.
   - Capture execution identifiers and current status.
3. Monitor execution.
   - Check the pipeline status (Idle vs Running).
   - Verify frames are rendered with predictions, inference output is generated as per sink configuration.
   - Record key runtime metrics if available (throughput & latency).
4. Validate output quality.
   - Spot-check predictions against known scenes or samples.
   - Confirm class distribution and confidence values are reasonable.
5. Handle degradation.
   - If source degrades: reconnect or switch to a known-good source.
   - If model output degrades: verify loaded model version and thresholds.
   - If sink fails: apply fallback sink.
