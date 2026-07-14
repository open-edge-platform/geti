# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

<#
.SYNOPSIS
    Upgrade an existing Docker-based Intel Geti deployment to a new image version on Windows.

.DESCRIPTION
    Performs a safe, reversible upgrade of a Docker-based Geti deployment:

      1. Takes a full snapshot of the persistent data volume before anything
         changes, so the previous state can always be restored (no data loss).
      2. Pulls the new image and recreates the container against the SAME
         data/logs volumes. On startup the backend migrates the database and
         on-disk data to the new version, rolling those back automatically on
         failure.
      3. Health-checks the new container. If it never becomes healthy (or the
         backend exits with the dedicated fatal-migration exit code 3), the whole
         deployment is rolled back to the previous image AND the previous data
         snapshot, leaving a fully usable installation.

    All actions are logged to a timestamped log file for troubleshooting.

.PARAMETER Accelerator
    Accelerator variant: cpu | xpu | cuda (default: cpu).

.PARAMETER Tag
    Image tag to upgrade to (default: latest).

.PARAMETER Registry
    Image registry/namespace (default: ghcr.io/open-edge-platform).

.PARAMETER Port
    Host port the app is served on (default: 7860).

.PARAMETER ContainerName
    Container name (default: geti-<accelerator>).

.PARAMETER DataVolume
    Named data volume to back up/restore (default: geti-data).

.PARAMETER HealthTimeout
    Seconds to wait for the new version to become healthy (default: 300).

.PARAMETER BackupDir
    Directory to store the pre-upgrade data snapshot (default: .\geti-upgrade-backups).

.PARAMETER NoDataBackup
    Skip the full data-volume snapshot (NOT recommended; relies solely on the
    backend's own DB rollback).

.PARAMETER KeepBackup
    Keep the data snapshot after a successful upgrade.

.PARAMETER Yes
    Assume yes to all prompts (non-interactive).

.EXAMPLE
    .\upgrade.ps1 -Accelerator xpu -Tag 3.1.0

.EXAMPLE
    .\upgrade.ps1 -Accelerator cpu -Tag latest -Yes
#>

[CmdletBinding()]
param(
    [Alias("a")]
    [ValidateSet("cpu", "xpu", "cuda")]
    [string]$Accelerator = "cpu",

    [Alias("t")]
    [string]$Tag = "latest",

    [Alias("r")]
    [string]$Registry = "ghcr.io/open-edge-platform",

    [Alias("p")]
    [int]$Port = 7860,

    [string]$ContainerName = "",

    [string]$DataVolume = "geti-data",

    [int]$HealthTimeout = 300,

    [string]$BackupDir = "$(Get-Location)\geti-upgrade-backups",

    [switch]$NoDataBackup,

    [switch]$KeepBackup,

    [Alias("y")]
    [switch]$Yes
)

$ErrorActionPreference = "Stop"

# Exit code the backend uses for a fatal, non-restartable migration failure
# (see application/backend/app/lifecycle.py:MIGRATION_FATAL_EXIT_CODE).
$script:MIGRATION_FATAL_EXIT_CODE = 3

$script:ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }

# ---------------------------------------------------------------------------
# Derived configuration
# ---------------------------------------------------------------------------
if ([string]::IsNullOrEmpty($ContainerName)) {
    $ContainerName = "geti-$Accelerator"
}
$script:LocalImage = "geti-${Accelerator}:${Tag}"
$script:RemoteImage = "${Registry}/geti-${Accelerator}:${Tag}"
$script:DataBackupEnabled = -not $NoDataBackup

New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
# Use [DateTime]::UtcNow rather than 'Get-Date -AsUTC' for Windows PowerShell 5.1 compatibility.
$script:Timestamp = ([DateTime]::UtcNow).ToString("yyyyMMddHHmmss")
$script:LogFile = Join-Path $BackupDir "upgrade-$($script:Timestamp).log"
$script:DataBackupFile = Join-Path $BackupDir "${DataVolume}-$($script:Timestamp).tar.gz"
"" | Set-Content -Path $script:LogFile

# Recorded rollback state.
$script:PreviousImageId = ""

# ---------------------------------------------------------------------------
# Logging helpers - everything is echoed to the console and the log file.
# ---------------------------------------------------------------------------
function Write-Log {
    param([string]$Message)
    $line = "{0} {1}" -f ([DateTime]::UtcNow).ToString("HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -Path $script:LogFile -Value $line
}

function Write-ErrorMessage {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

function Invoke-Logged {
    # Run an external command, streaming output to the log (and console in
    # verbose mode). Throws on a non-zero exit code.
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        if ($VerbosePreference -eq "Continue") {
            & $Command @Arguments 2>&1 | ForEach-Object {
                Write-Host $_
                Add-Content -Path $script:LogFile -Value ($_ | Out-String).TrimEnd()
            }
        } else {
            & $Command @Arguments *>> $script:LogFile
        }
    } finally {
        $ErrorActionPreference = $prevEAP
    }

    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        throw "Command '$Command $($Arguments -join ' ')' failed with exit code $LASTEXITCODE"
    }
}

function Confirm-Prompt {
    param([string]$Prompt)
    if ($Yes) { return $true }
    $response = Read-Host "$Prompt [Y/n]"
    if ($response -match "^n(o)?$") { return $false }
    return $true
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
function Test-Preflight {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "docker is not installed. Please install Docker Desktop and try again."
    }
    # Verify the Docker daemon is reachable.
    & docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "The Docker daemon is not reachable. Is Docker Desktop running?"
    }
    Write-Log "Upgrade target: $($script:RemoteImage) -> container '$ContainerName' on port $Port"
    Write-Log "Log file: $($script:LogFile)"
}

function Get-ContainerState {
    # Returns the container's status (e.g. running, exited) or empty if absent.
    $state = (& docker inspect -f '{{.State.Status}}' $ContainerName 2>$null)
    if ($LASTEXITCODE -ne 0) { return "" }
    return ($state | Select-Object -First 1)
}

function Get-ContainerExitCode {
    $code = (& docker inspect -f '{{.State.ExitCode}}' $ContainerName 2>$null)
    if ($LASTEXITCODE -ne 0) { return $null }
    return [int]($code | Select-Object -First 1)
}

# ---------------------------------------------------------------------------
# Rollback point capture
# ---------------------------------------------------------------------------
function Save-RollbackPoint {
    # 1. Remember the image ID currently backing the local tag so we can restore
    #    it even after the tag is overwritten by the freshly pulled image.
    $script:PreviousImageId = (& docker image inspect -f '{{.Id}}' $script:LocalImage 2>$null | Select-Object -First 1)
    if ($LASTEXITCODE -ne 0) { $script:PreviousImageId = "" }

    if ($script:PreviousImageId) {
        Write-Log "Recorded previous image: $($script:PreviousImageId)"
    } else {
        Write-Log "No existing local image '$($script:LocalImage)' found (first Docker install?)."
    }

    # 2. Snapshot the persistent data volume so the exact pre-upgrade state can
    #    be restored regardless of what the migration does.
    if (-not $script:DataBackupEnabled) {
        Write-Log "WARNING: -NoDataBackup set; skipping full data-volume snapshot."
        return
    }

    & docker volume inspect $DataVolume *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Data volume '$DataVolume' does not exist yet; nothing to snapshot."
        $script:DataBackupEnabled = $false
        return
    }

    Write-Log "Snapshotting data volume '$DataVolume' -> $($script:DataBackupFile) ..."
    Write-Log "(This may take a while and disk space proportional to your data size.)"
    $backupName = Split-Path -Leaf $script:DataBackupFile
    Invoke-Logged -Command "docker" -Arguments @(
        "run", "--rm",
        "-v", "${DataVolume}:/data:ro",
        "-v", "${BackupDir}:/backup",
        "alpine", "sh", "-c", "tar czf /backup/$backupName -C /data ."
    )
    Write-Log "OK Data snapshot created."
}

# ---------------------------------------------------------------------------
# Start the container from the current local image (delegates to just run-image
# so all device / GPU / port wiring stays in one place).
# ---------------------------------------------------------------------------
function Start-Container {
    if (-not (Get-Command just -ErrorAction SilentlyContinue)) {
        throw "'just' is required to (re)start the container. Install it from https://github.com/casey/just"
    }
    $justfile = Join-Path $script:ScriptDir "application\Justfile"
    Write-Log "Starting container '$ContainerName' from image '$($script:LocalImage)'..."
    Invoke-Logged -Command "just" -Arguments @(
        "--justfile", $justfile, "run-image",
        "--accelerator", $Accelerator,
        "--tag", $Tag,
        "--port", "$Port",
        "--name", $ContainerName,
        "--detach", "true",
        "--reload", "true"
    )
}

# ---------------------------------------------------------------------------
# Health verification of the running container.
# ---------------------------------------------------------------------------
function Test-Health {
    # The backend serves /health over HTTPS with a self-signed cert, so
    # certificate validation must be bypassed. Prefer curl.exe (ships with
    # Windows 10 1803+); fall back to Invoke-WebRequest with a cert-check bypass.
    $url = "https://localhost:${Port}/health"

    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($curl) {
        & curl.exe -ksSf --max-time 5 $url *> $null
        return ($LASTEXITCODE -eq 0)
    }

    try {
        if ($PSVersionTable.PSVersion.Major -ge 6) {
            $null = Invoke-WebRequest -Uri $url -TimeoutSec 5 -SkipCertificateCheck -UseBasicParsing
        } else {
            # Windows PowerShell 5.1: bypass certificate validation process-wide.
            $prevCallback = [System.Net.ServicePointManager]::ServerCertificateValidationCallback
            [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
            try {
                $null = Invoke-WebRequest -Uri $url -TimeoutSec 5 -UseBasicParsing
            } finally {
                [System.Net.ServicePointManager]::ServerCertificateValidationCallback = $prevCallback
            }
        }
        return $true
    } catch {
        return $false
    }
}

function Wait-Healthy {
    Write-Log "Waiting up to ${HealthTimeout}s for the new version to become healthy..."
    $deadline = (Get-Date).AddSeconds($HealthTimeout)
    while ((Get-Date) -lt $deadline) {
        $state = Get-ContainerState
        if ($state -eq "exited" -or $state -eq "dead") {
            $code = Get-ContainerExitCode
            if ($code -eq $script:MIGRATION_FATAL_EXIT_CODE) {
                Write-Log "FAIL Backend exited with fatal migration code ${code}: upgrade cannot proceed."
            } else {
                Write-Log "FAIL Container exited unexpectedly (exit code ${code})."
            }
            (& docker logs --tail 50 $ContainerName 2>&1) | Add-Content -Path $script:LogFile
            return $false
        }
        if (Test-Health) {
            Write-Log "OK New version is healthy."
            return $true
        }
        Start-Sleep -Seconds 3
    }
    Write-Log "FAIL Timed out waiting for the new version to become healthy."
    (& docker logs --tail 50 $ContainerName 2>&1) | Add-Content -Path $script:LogFile
    return $false
}

# ---------------------------------------------------------------------------
# Rollback: restore the previous image + previous data, and restart.
# ---------------------------------------------------------------------------
function Invoke-Rollback {
    Write-Log "----------------------------------------------"
    Write-Log "Rolling back to the previous version..."

    # Stop and remove the failed new container.
    & docker rm -f $ContainerName *> $null

    # Restore the previous data snapshot (belt-and-suspenders on top of the
    # backend's own automatic DB/filesystem rollback).
    if ($script:DataBackupEnabled -and (Test-Path $script:DataBackupFile)) {
        Write-Log "Restoring data volume '$DataVolume' from snapshot..."
        $backupName = Split-Path -Leaf $script:DataBackupFile
        Invoke-Logged -Command "docker" -Arguments @(
            "run", "--rm",
            "-v", "${DataVolume}:/data",
            "-v", "${BackupDir}:/backup",
            "alpine", "sh", "-c",
            "rm -rf /data/* /data/..?* /data/.[!.]* 2>/dev/null; tar xzf /backup/$backupName -C /data"
        )
        Write-Log "OK Data restored to its pre-upgrade state."
    }

    # Restore the previous image tag.
    if ($script:PreviousImageId) {
        Write-Log "Restoring previous image tag '$($script:LocalImage)'..."
        Invoke-Logged -Command "docker" -Arguments @("tag", $script:PreviousImageId, $script:LocalImage)
        Start-Container
        if (Wait-Healthy) {
            Write-Log "OK Rollback complete. The previous version is running and usable."
        } else {
            Write-Log "FAIL The previous version did not come up cleanly. Check $($script:LogFile)."
            Write-Log "     Your data snapshot is preserved at $($script:DataBackupFile)."
        }
    } else {
        Write-Log "No previous image to restore. Your data snapshot is preserved at $($script:DataBackupFile)."
    }

    Write-Log "Upgrade failed and was rolled back. See $($script:LogFile) for details."
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
function Main {
    Write-Host ""
    Write-Host "Intel Geti Upgrade (Windows/PowerShell)" -ForegroundColor Green
    Write-Host "=======================================" -ForegroundColor Green
    Write-Host ""

    Test-Preflight

    if (-not (Confirm-Prompt "Upgrade '$ContainerName' to $($script:RemoteImage)?")) {
        Write-Host "Upgrade cancelled."
        return
    }

    Save-RollbackPoint

    Write-Log "Pulling $($script:RemoteImage)..."
    try {
        Invoke-Logged -Command "docker" -Arguments @("pull", $script:RemoteImage)
    } catch {
        Write-Log "FAIL Failed to pull $($script:RemoteImage). Nothing was changed."
        exit 1
    }
    Invoke-Logged -Command "docker" -Arguments @("tag", $script:RemoteImage, $script:LocalImage)

    # From here on, any failure triggers a rollback.
    try {
        Start-Container

        if (Wait-Healthy) {
            Write-Log "OK Upgrade to $($script:RemoteImage) completed successfully."
            if ($script:DataBackupEnabled -and (Test-Path $script:DataBackupFile)) {
                if ($KeepBackup) {
                    Write-Log "Data snapshot kept at $($script:DataBackupFile)."
                } else {
                    Remove-Item -Path $script:DataBackupFile -Force -ErrorAction SilentlyContinue
                    Write-Log "Removed pre-upgrade data snapshot (pass -KeepBackup to retain it)."
                }
            }
            Write-Log "Geti is available at: https://localhost:${Port}"
            return
        }

        # Health check failed -> rollback.
        Invoke-Rollback
        exit 1
    } catch {
        Write-Log "FAIL Upgrade error: $_"
        Invoke-Rollback
        exit 1
    }
}

try {
    Main
} catch {
    Write-Host ""
    Write-ErrorMessage "Upgrade failed: $_"
    if (Test-Path $script:LogFile) {
        Write-Host "Check $($script:LogFile) for details."
    }
    exit 1
}

