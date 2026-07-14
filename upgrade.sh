#!/bin/bash
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
# Upgrade an existing Docker-based Intel Geti deployment to a new image version.
#
# The upgrade is safe and reversible:
#   1. A full snapshot of the persistent data volume is taken before anything
#      changes, so the previous state can always be restored (no data loss).
#   2. The new image is pulled and the container is recreated against the SAME
#      data/logs volumes. On startup the backend migrates the database + on-disk
#      data to the new version, automatically rolling those back on failure.
#   3. The new container is health-checked. If it never becomes healthy (or the
#      backend exits with the dedicated fatal-migration exit code), the whole
#      deployment is rolled back to the previous image AND the previous data
#      snapshot, leaving a fully usable installation.
#
# All actions are logged to a timestamped log file for troubleshooting.

set -Eeuo pipefail

# Exit code the backend uses for a fatal, non-restartable migration failure
# (see application/backend/app/lifecycle.py:MIGRATION_FATAL_EXIT_CODE).
readonly MIGRATION_FATAL_EXIT_CODE=3

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Upgrade a Docker-based Intel Geti deployment to a new image version, with
automatic rollback on failure.

Options:
  -a, --accelerator   Accelerator variant: cpu | xpu | cuda (default: cpu)
  -t, --tag           Image tag to upgrade to (default: latest)
  -r, --registry      Image registry/namespace
                      (default: ghcr.io/open-edge-platform)
  -p, --port          Host port the app is served on (default: 7860)
      --container-name Container name (default: geti-<accelerator>)
      --data-volume   Named data volume to back up/restore (default: geti-data)
      --health-timeout Seconds to wait for the new version to become healthy
                      (default: 300)
      --backup-dir    Directory to store the pre-upgrade data snapshot
                      (default: ./geti-upgrade-backups)
      --no-data-backup Skip the full data-volume snapshot (NOT recommended;
                      relies solely on the backend's own DB rollback)
      --keep-backup   Keep the data snapshot after a successful upgrade
  -y, --yes           Assume yes to all prompts (non-interactive)
  -v, --verbose       Show detailed output
  -h, --help          Show this help and exit

Examples:
  $(basename "$0") --accelerator xpu --tag 3.1.0
  $(basename "$0") -a cpu -t latest -y
EOF
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
parse_args() {
    ACCELERATOR="cpu"
    TAG="latest"
    REGISTRY="ghcr.io/open-edge-platform"
    PORT="7860"
    CONTAINER_NAME=""
    DATA_VOLUME="geti-data"
    HEALTH_TIMEOUT="300"
    BACKUP_DIR="$(pwd)/geti-upgrade-backups"
    DATA_BACKUP=1
    KEEP_BACKUP=""
    ASSUME_YES=""
    VERBOSE=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -a|--accelerator) ACCELERATOR="$2"; shift 2 ;;
            -t|--tag) TAG="$2"; shift 2 ;;
            -r|--registry) REGISTRY="$2"; shift 2 ;;
            -p|--port) PORT="$2"; shift 2 ;;
            --container-name) CONTAINER_NAME="$2"; shift 2 ;;
            --data-volume) DATA_VOLUME="$2"; shift 2 ;;
            --health-timeout) HEALTH_TIMEOUT="$2"; shift 2 ;;
            --backup-dir) BACKUP_DIR="$2"; shift 2 ;;
            --no-data-backup) DATA_BACKUP=""; shift ;;
            --keep-backup) KEEP_BACKUP=1; shift ;;
            -y|--yes) ASSUME_YES=1; shift ;;
            -v|--verbose) VERBOSE=1; shift ;;
            -h|--help) usage; exit 0 ;;
            *) echo "Error: unknown option '$1'" >&2; usage; exit 1 ;;
        esac
    done

    case "$ACCELERATOR" in
        cpu|xpu|cuda) ;;
        *) echo "Error: --accelerator must be one of cpu|xpu|cuda" >&2; exit 1 ;;
    esac

    if [[ -z "$CONTAINER_NAME" ]]; then
        CONTAINER_NAME="geti-${ACCELERATOR}"
    fi
    LOCAL_IMAGE="geti-${ACCELERATOR}:${TAG}"
    REMOTE_IMAGE="${REGISTRY}/geti-${ACCELERATOR}:${TAG}"

    mkdir -p "$BACKUP_DIR"
    TIMESTAMP="$(date -u +%Y%m%d%H%M%S)"
    LOG_FILE="${BACKUP_DIR}/upgrade-${TIMESTAMP}.log"
    DATA_BACKUP_FILE="${BACKUP_DIR}/${DATA_VOLUME}-${TIMESTAMP}.tar.gz"
    : > "$LOG_FILE"
}

# ---------------------------------------------------------------------------
# Logging helpers — everything is echoed to the console and the log file.
# ---------------------------------------------------------------------------
log() {
    printf '%s %s\n' "$(date -u +%H:%M:%S)" "$*" | tee -a "$LOG_FILE"
}

run() {
    # Run a command, streaming output to the log (and console in verbose mode).
    if [[ -n "$VERBOSE" ]]; then
        "$@" 2>&1 | tee -a "$LOG_FILE"
    else
        "$@" >>"$LOG_FILE" 2>&1
    fi
}

confirm() {
    local prompt="$1"
    [[ -n "$ASSUME_YES" ]] && return 0
    local response
    read -rp "$prompt [Y/n]: " response </dev/tty || return 1
    [[ "${response,,}" =~ ^n(o)?$ ]] && return 1
    return 0
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
preflight() {
    command -v docker >/dev/null 2>&1 || { echo "Error: docker is not installed." >&2; exit 1; }
    docker info >/dev/null 2>&1 || { echo "Error: the Docker daemon is not reachable." >&2; exit 1; }
    log "Upgrade target: ${REMOTE_IMAGE} → container '${CONTAINER_NAME}' on port ${PORT}"
    log "Log file: ${LOG_FILE}"
}

container_state() {
    # Prints the container's status (e.g. running, exited) or empty if absent.
    docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME" 2>/dev/null || true
}

container_exit_code() {
    docker inspect -f '{{.State.ExitCode}}' "$CONTAINER_NAME" 2>/dev/null || echo ""
}

# ---------------------------------------------------------------------------
# Rollback point capture
# ---------------------------------------------------------------------------
capture_rollback_point() {
    # 1. Remember the image ID currently backing the local tag so we can restore
    #    it even after the tag is overwritten by the freshly pulled image.
    PREVIOUS_IMAGE_ID="$(docker image inspect -f '{{.Id}}' "$LOCAL_IMAGE" 2>/dev/null || true)"
    if [[ -n "$PREVIOUS_IMAGE_ID" ]]; then
        log "Recorded previous image: ${PREVIOUS_IMAGE_ID}"
    else
        log "No existing local image '${LOCAL_IMAGE}' found (first Docker install?)."
    fi

    # 2. Snapshot the persistent data volume so the exact pre-upgrade state can
    #    be restored regardless of what the migration does.
    if [[ -z "$DATA_BACKUP" ]]; then
        log "WARNING: --no-data-backup set; skipping full data-volume snapshot."
        return
    fi
    if ! docker volume inspect "$DATA_VOLUME" >/dev/null 2>&1; then
        log "Data volume '${DATA_VOLUME}' does not exist yet; nothing to snapshot."
        DATA_BACKUP=""
        return
    fi

    log "Snapshotting data volume '${DATA_VOLUME}' → ${DATA_BACKUP_FILE} ..."
    log "(This may take a while and disk space proportional to your data size.)"
    run docker run --rm \
        -v "${DATA_VOLUME}:/data:ro" \
        -v "${BACKUP_DIR}:/backup" \
        alpine sh -c "tar czf /backup/$(basename "$DATA_BACKUP_FILE") -C /data ."
    log "✓ Data snapshot created."
}

# ---------------------------------------------------------------------------
# Start the container from the current local image (delegates to just run-image
# so all device / GPU / port wiring stays in one place).
# ---------------------------------------------------------------------------
start_container() {
    if ! command -v just >/dev/null 2>&1; then
        echo "Error: 'just' is required to (re)start the container. Install it from https://github.com/casey/just" >&2
        exit 1
    fi
    log "Starting container '${CONTAINER_NAME}' from image '${LOCAL_IMAGE}'..."
    run just --justfile "${SCRIPT_DIR}/application/Justfile" run-image \
        --accelerator "$ACCELERATOR" \
        --tag "$TAG" \
        --port "$PORT" \
        --name "$CONTAINER_NAME" \
        --detach true \
        --reload true
}

# ---------------------------------------------------------------------------
# Health verification of the running container.
# ---------------------------------------------------------------------------
wait_until_healthy() {
    log "Waiting up to ${HEALTH_TIMEOUT}s for the new version to become healthy..."
    local deadline=$(( $(date +%s) + HEALTH_TIMEOUT ))
    while (( $(date +%s) < deadline )); do
        local state
        state="$(container_state)"
        if [[ "$state" == "exited" || "$state" == "dead" ]]; then
            local code
            code="$(container_exit_code)"
            if [[ "$code" == "$MIGRATION_FATAL_EXIT_CODE" ]]; then
                log "✗ Backend exited with fatal migration code ${code}: upgrade cannot proceed."
            else
                log "✗ Container exited unexpectedly (exit code ${code})."
            fi
            docker logs --tail 50 "$CONTAINER_NAME" >>"$LOG_FILE" 2>&1 || true
            return 1
        fi
        # The backend serves /health over HTTPS with a self-signed cert (-k).
        if curl -ksSf --max-time 5 "https://localhost:${PORT}/health" >/dev/null 2>&1; then
            log "✓ New version is healthy."
            return 0
        fi
        sleep 3
    done
    log "✗ Timed out waiting for the new version to become healthy."
    docker logs --tail 50 "$CONTAINER_NAME" >>"$LOG_FILE" 2>&1 || true
    return 1
}

# ---------------------------------------------------------------------------
# Rollback: restore the previous image + previous data, and restart.
# ---------------------------------------------------------------------------
rollback() {
    log "──────────────────────────────────────────────"
    log "Rolling back to the previous version..."

    # Stop and remove the failed new container.
    docker rm -f "$CONTAINER_NAME" >>"$LOG_FILE" 2>&1 || true

    # Restore the previous data snapshot (belt-and-suspenders on top of the
    # backend's own automatic DB/filesystem rollback).
    if [[ -n "$DATA_BACKUP" && -f "$DATA_BACKUP_FILE" ]]; then
        log "Restoring data volume '${DATA_VOLUME}' from snapshot..."
        run docker run --rm \
            -v "${DATA_VOLUME}:/data" \
            -v "${BACKUP_DIR}:/backup" \
            alpine sh -c "rm -rf /data/* /data/..?* /data/.[!.]* 2>/dev/null; tar xzf /backup/$(basename "$DATA_BACKUP_FILE") -C /data"
        log "✓ Data restored to its pre-upgrade state."
    fi

    # Restore the previous image tag.
    if [[ -n "$PREVIOUS_IMAGE_ID" ]]; then
        log "Restoring previous image tag '${LOCAL_IMAGE}'..."
        run docker tag "$PREVIOUS_IMAGE_ID" "$LOCAL_IMAGE"
        start_container
        if wait_until_healthy; then
            log "✓ Rollback complete. The previous version is running and usable."
        else
            log "✗ The previous version did not come up cleanly. Check ${LOG_FILE}."
            log "  Your data snapshot is preserved at ${DATA_BACKUP_FILE}."
        fi
    else
        log "No previous image to restore. Your data snapshot is preserved at ${DATA_BACKUP_FILE}."
    fi

    log "Upgrade failed and was rolled back. See ${LOG_FILE} for details."
    exit 1
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    parse_args "$@"
    preflight

    if ! confirm "Upgrade '${CONTAINER_NAME}' to ${REMOTE_IMAGE}?"; then
        echo "Upgrade cancelled."
        exit 0
    fi

    capture_rollback_point

    log "Pulling ${REMOTE_IMAGE}..."
    if ! run docker pull "$REMOTE_IMAGE"; then
        log "✗ Failed to pull ${REMOTE_IMAGE}. Nothing was changed."
        exit 1
    fi
    run docker tag "$REMOTE_IMAGE" "$LOCAL_IMAGE"

    # From here on, any failure triggers a rollback.
    trap 'rollback' ERR

    start_container

    if wait_until_healthy; then
        trap - ERR
        log "✓ Upgrade to ${REMOTE_IMAGE} completed successfully."
        if [[ -n "$DATA_BACKUP" && -f "$DATA_BACKUP_FILE" ]]; then
            if [[ -n "$KEEP_BACKUP" ]]; then
                log "Data snapshot kept at ${DATA_BACKUP_FILE}."
            else
                rm -f "$DATA_BACKUP_FILE"
                log "Removed pre-upgrade data snapshot (pass --keep-backup to retain it)."
            fi
        fi
        log "Geti is available at: https://localhost:${PORT}"
        exit 0
    fi

    # Health check failed → rollback (also reachable via the ERR trap).
    trap - ERR
    rollback
}

main "$@"

