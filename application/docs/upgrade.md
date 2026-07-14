# Upgrading Intel Geti

This guide explains how to upgrade an existing Intel Geti installation to a newer
version while preserving your projects, datasets and models, and how the upgrade
is rolled back automatically if something goes wrong.

> **Guarantee:** An upgrade never deletes your data. If migration fails, both the
> application and its data are reverted to the previous version, which stays fully
> usable.

## Table of contents

1. [How upgrades work](#how-upgrades-work)
2. [Docker deployment](#docker-deployment)
3. [Windows desktop (MSIX) app](#windows-desktop-msix-app)
4. [Source installation](#source-installation)
5. [What happens on failure (rollback)](#what-happens-on-failure-rollback)
6. [Downgrading](#downgrading)
7. [Troubleshooting](#troubleshooting)

---

## How upgrades work

Geti stores all persistent state in a **data directory** (`DATA_DIR`, mounted as
the `geti-data` Docker volume or a per-user directory for the desktop app):

- a SQLite database `geti.db` (project/model/dataset metadata), and
- binary artifacts on the filesystem (media, model weights, dataset revisions).

Every release pins the data layout to an Alembic **revision** — the single source
of truth for both the database schema and the on-disk layout (see
[`migration-guidelines.md`](./migration-guidelines.md)). When a newer version
starts, it automatically:

1. Records/checks the data version (a small `.geti_data_version` stamp file in the
   data directory identifies which version the data was last brought up to).
2. Takes a **backup of the database** before migrating.
3. Runs the migrations (`alembic upgrade head`), which update the schema and move
   any files in lockstep.
4. Advances the recorded data version.

Because migration runs on startup, **upgrading is simply a matter of replacing the
application with the newer version and starting it** — the data migration happens
by itself, with automatic rollback on failure.

---

## Docker deployment

The Docker image bundles the whole application. The persistent `geti-data` and
`geti-logs` volumes are **not** part of the image, so replacing the image with a
newer one and reusing the same volumes preserves all your data.

### Recommended: the `upgrade.sh` script

The repository ships an [`upgrade.sh`](../../upgrade.sh) helper (and a Windows
PowerShell equivalent, [`upgrade.ps1`](../../upgrade.ps1)) that performs a safe,
verifiable upgrade with automatic rollback:

```bash
# Linux / macOS / WSL — from the repository root
./upgrade.sh --accelerator xpu --tag 3.1.0
```

```powershell
# Windows (Docker Desktop) — from the repository root
.\upgrade.ps1 -Accelerator xpu -Tag 3.1.0
```

It will:

1. **Snapshot** the `geti-data` volume so the exact pre-upgrade state can be
   restored (skip with `--no-data-backup` / `-NoDataBackup` if you manage backups
   yourself).
2. Record the currently deployed image for rollback.
3. Pull the requested image and recreate the container against the same volumes.
4. **Health-check** the new version (`https://localhost:<port>/health`). It also
   detects the backend's dedicated fatal-migration exit code (`3`).
5. On success, report completion. On failure, **roll back** to the previous image
   _and_ the previous data snapshot, then restart the previous version.

All steps are written to a timestamped log under `./geti-upgrade-backups/` for
troubleshooting. Run `./upgrade.sh --help` (or `Get-Help .\upgrade.ps1 -Detailed`)
for all options.

> **Windows note:** `upgrade.ps1` drives Docker Desktop and uses the `just` > `run-image` recipe, which runs a Bash recipe — ensure `just` and a Bash
> interpreter (e.g. Git Bash / WSL) are available on `PATH`. It works on both
> Windows PowerShell 5.1 and PowerShell 7+.

### Manual upgrade

If you prefer to upgrade by hand:

```bash
# 1. (Recommended) Back up the data volume
docker run --rm -v geti-data:/data -v "$PWD":/backup alpine \
    tar czf /backup/geti-data-backup.tar.gz -C /data .

# 2. Pull the new image and retag it
docker pull ghcr.io/open-edge-platform/geti-cpu:3.1.0
docker tag  ghcr.io/open-edge-platform/geti-cpu:3.1.0 geti-cpu:latest

# 3. Recreate the container against the SAME volumes (data is migrated on startup)
just run-image --accelerator cpu --reload --detach true

# 4. Verify
curl -k https://localhost:7860/health
```

To restore the backup after a manual upgrade problem, see
[Downgrading](#downgrading).

---

## Windows desktop (MSIX) app

The MSIX package contains the UI and the bundled backend. Your projects and models
live in a **per-user data directory** that is deliberately kept **outside** the
install location (e.g. `%LOCALAPPDATA%\com.intel.geti`), so it survives app
updates.

To upgrade:

1. Download and run the newer `.msix` installer (or let Windows auto-update the
   package). Windows replaces the app in place, keeping your data directory.
2. Launch Geti. On first start the bundled backend migrates your data to the new
   version, taking a database backup first.

If the migration fails, the backend automatically rolls the data back to the
previous version and exits. Because the previous package can be reinstalled and
your data was reverted, the app remains usable — simply reinstall the previous
`.msix` version (see [Downgrading](#downgrading)).

---

## Source installation

If you installed from source with `install.sh` / `install.ps1`, re-running the
installer checks out the newer release and rebuilds the app. Starting it runs the
same on-startup migration (with automatic rollback) against your existing
`data/` directory.

```bash
./install.sh        # pulls the pinned release, rebuilds, and starts Geti
```

---

## What happens on failure (rollback)

A migration failure is treated as **fatal and non-restartable** — retrying would
fail identically — so the backend:

1. Rolls the data back to the pre-upgrade state:
   - reverts the migrations (`alembic downgrade` to the starting revision), which
     also undoes any in-script file moves, then
   - restores the database from the pre-upgrade backup as the authoritative safety
     net.
2. Logs detailed recovery guidance (including the backup location).
3. Exits with the dedicated code `3` so launchers/supervisors do **not** restart
   it in a loop.

At the deployment level, `upgrade.sh` additionally restores the full data-volume
snapshot and the previous image, so a failed Docker upgrade ends with the previous
version running and usable.

---

## Downgrading

- **Docker:** point the container back at the previous image tag and, if needed,
  restore your data snapshot:

  ```bash
  docker rm -f geti-cpu
  docker run --rm -v geti-data:/data -v "$PWD":/backup alpine \
      sh -c 'rm -rf /data/* && tar xzf /backup/geti-data-backup.tar.gz -C /data'
  docker tag ghcr.io/open-edge-platform/geti-cpu:3.0.0 geti-cpu:latest
  just run-image --accelerator cpu --reload --detach true
  ```

- **MSIX:** uninstall the current package and install the previous `.msix`. Your
  per-user data directory is preserved. If you had upgraded and rolled back, the
  data is already at the previous version.

> **Note:** Downgrading across a version that changed the data layout requires a
> data snapshot taken _before_ the upgrade — the newer layout is generally not
> readable by older versions. `upgrade.sh` creates this snapshot automatically.

---

## Troubleshooting

- **Where are the logs?**
  - Docker: `./geti-upgrade-backups/upgrade-<timestamp>.log` (from `upgrade.sh`)
    and the container logs (`docker logs geti-cpu`) / the `geti-logs` volume.
  - Desktop: the per-user log directory (e.g. `%LOCALAPPDATA%\com.intel.geti\logs`).
- **The new version won't start after an upgrade.** Check the logs for a
  `Fatal application upgrade error` message. The data has been rolled back; start
  the previous version to continue, and open an issue at
  https://github.com/open-edge-platform/geti with the log attached.
- **A pre-upgrade database backup (`geti.db.<timestamp>.bak`) is left in the data
  directory.** This is retained on purpose after a failed upgrade for diagnostics.
  You can delete it once the previous version is confirmed working.
