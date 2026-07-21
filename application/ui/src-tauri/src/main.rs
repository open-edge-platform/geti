// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod backend;

use std::process::Child;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};

use serde::Deserialize;
use tauri::{AppHandle, Manager, RunEvent, WindowEvent};
use tauri_plugin_dialog::{DialogExt, MessageDialogButtons, MessageDialogKind};
use tauri_plugin_opener::OpenerExt;

use crate::backend::spawn_backend;

/// Public issue tracker where users can report fatal backend failures.
///
/// Native Windows dialogs render their body as non-selectable plain text, so a
/// URL printed there can neither be clicked nor copied. Instead of relying on
/// the user to type it out, the fatal dialogs offer a button that opens this URL
/// in the default browser (see [`open_issue_tracker`]). Keep it in the
/// `opener:allow-open-url` allowlist in `capabilities/default.json`.
const ISSUE_TRACKER_URL: &str = "https://github.com/open-edge-platform/geti/issues";

/// Open the issue tracker in the user's default browser, logging on failure.
fn open_issue_tracker(app: &AppHandle) {
    if let Err(e) = app.opener().open_url(ISSUE_TRACKER_URL, None::<String>) {
        log::warn!("Failed to open issue tracker URL {ISSUE_TRACKER_URL:?}: {e}");
    }
}

/// Exit code the backend uses to signal a fatal, non-restartable data-migration
/// failure during an in-place upgrade (see
/// `application/backend/app/lifecycle.py:MIGRATION_FATAL_EXIT_CODE`). Before
/// exiting with this code the backend has already rolled its data back to the
/// previous version, so the *previous* release remains usable — the newer one
/// simply cannot run against the existing data.
const MIGRATION_FATAL_EXIT_CODE: i32 = 3;

/// Name of the machine-readable status file the backend writes into `DATA_DIR`
/// right before it exits with `MIGRATION_FATAL_EXIT_CODE`. Keep this name and
/// schema in sync with `application/backend/app/lifecycle.py:FATAL_STATUS_FILENAME`.
const FATAL_STATUS_FILENAME: &str = "fatal_status.json";

/// Structured description of a fatal backend startup failure, deserialized from
/// [`FATAL_STATUS_FILENAME`]. Unknown fields are ignored so the backend can
/// extend the schema without breaking older shells.
#[derive(Debug, Default, Deserialize)]
struct FatalStatus {
    /// Machine-readable failure category, e.g. `"migration"`.
    #[serde(default)]
    fatal: String,
    /// Absolute path of the pre-migration backup to restore, if one was taken.
    #[serde(default)]
    backup_path: Option<String>,
    /// Absolute path of the database file the backup should be restored to.
    #[serde(default)]
    database_path: Option<String>,
}

/// Read and remove the backend's fatal-status file from `app_local_data_dir()`.
///
/// Returns `None` if the file is absent or unreadable. The file is always
/// deleted after a successful read so a stale status can't resurface on the next
/// launch; the backend also clears it on a healthy start as a second safeguard.
fn read_and_clear_fatal_status(app: &AppHandle) -> Option<FatalStatus> {
    let path = app.path().app_local_data_dir().ok()?.join(FATAL_STATUS_FILENAME);
    let contents = std::fs::read_to_string(&path).ok()?;

    let status = serde_json::from_str::<FatalStatus>(&contents)
        .map_err(|e| log::warn!("Failed to parse fatal status file {path:?}: {e}"))
        .ok();

    if let Some(status) = &status {
        log::info!("Read fatal status file {path:?}: reason={:?}", status.fatal);
    }

    if let Err(e) = std::fs::remove_file(&path) {
        log::warn!("Failed to remove fatal status file {path:?}: {e}");
    }

    status
}

/// Shared handle used to tear the backend down and to tell the monitor thread
/// whether an exit was intentional (so it doesn't mistake a clean shutdown for a
/// crash).
#[derive(Clone, Default)]
struct BackendControl {
    /// PID of the spawned side-car, used to kill its whole process tree.
    pid: Arc<Mutex<Option<u32>>>,
    /// Set before we deliberately kill the backend during app shutdown.
    shutting_down: Arc<AtomicBool>,
}

/// Kill a process and all its descendants by PID.
///
/// - **Windows**: `taskkill /F /T /PID` terminates the entire process tree.
/// - **Unix**: sends `SIGKILL` to the process group (`kill -- -<pid>`). The
///   backend is spawned as its own process-group leader (see `backend.rs`), so
///   all of its multiprocessing workers are included.
fn kill_process_tree(pid: u32) {
    #[cfg(windows)]
    {
        use std::process::Command;
        let _ = Command::new("taskkill")
            .args(["/F", "/T", "/PID", &pid.to_string()])
            .output();
    }

    #[cfg(unix)]
    {
        use std::process::Command;
        // kill -- -PID sends the signal to the whole process group.
        let _ = Command::new("kill")
            .args(["-9", "--", &format!("-{pid}")])
            .output();
    }
}

/// Deliberately terminate the backend (app shutdown). Marks the exit as intended
/// so the monitor thread stays silent instead of showing a crash dialog.
fn shutdown_backend(control: &BackendControl) {
    control.shutting_down.store(true, Ordering::SeqCst);
    if let Some(pid) = control.pid.lock().unwrap().take() {
        kill_process_tree(pid);
        log::info!("⛔ Backend terminated");
    }
}

/// Resolve the per-user log directory as a display string for user-facing
/// messages, falling back to a generic phrase if it can't be resolved.
fn log_dir_hint(app: &AppHandle) -> String {
    app.path()
        .app_log_dir()
        .ok()
        .map(|p| p.display().to_string())
        .unwrap_or_else(|| "the application log directory".to_string())
}

/// Detailed message shown when the backend aborts an in-place upgrade because
/// the data migration failed (exit code 3). When the backend provided a
/// [`FatalStatus`] with a backup path, the exact recovery instructions are
/// included so the user can restore their data by hand if needed.
fn show_migration_failure_dialog(app: &AppHandle, status: Option<&FatalStatus>) {
    let log_dir = log_dir_hint(app);

    // Build the "how to recover your data" paragraph from whatever the backend
    // told us. The backend restores the backup automatically on its side, but we
    // still surface the exact file so a user can recover manually if that failed.
    let recovery = match status.and_then(|s| s.backup_path.as_deref()) {
        Some(backup_path) => {
            let db_target = status
                .and_then(|s| s.database_path.as_deref())
                .map(|db| format!("'{db}' (the original database file)"))
                .unwrap_or_else(|| "the original database file".to_string());
            format!(
                "To recover, restore the pre-migration database backup: rename the backup file \
'{backup_path}' back to {db_target}, overwriting the partially migrated database. After \
restoring the backup, downgrade the application to the previous version."
            )
        }
        None => String::new(),
    };

    let message = format!(
        "Geti tried to upgrade your data to this newer version, but the upgrade did not \
succeed.\n\n\
The newer version of Geti cannot run with your existing data and will now close.\n\n\
{recovery}\n\n\
Logs are available at:\n  {log_dir}\n\n\
If the problem persists, you can report it on our issue tracker and attach the log files."
    );

    let report = app
        .dialog()
        .message(message)
        .title("Geti upgrade failed")
        .kind(MessageDialogKind::Error)
        .buttons(MessageDialogButtons::OkCancelCustom(
            "Report issue".to_string(),
            "Close".to_string(),
        ))
        .blocking_show();

    if report {
        open_issue_tracker(app);
    }
}

/// Generic message shown when the backend stops unexpectedly for any other
/// reason, so the UI never just hangs with a dead backend.
fn show_backend_crash_dialog(app: &AppHandle, code: Option<i32>) {
    let log_dir = log_dir_hint(app);
    let code_str = code
        .map(|c| c.to_string())
        .unwrap_or_else(|| "unknown".to_string());
    let message = format!(
        "The Geti backend stopped unexpectedly (exit code {code_str}) and the application \
will now close.\n\n\
Please review the logs for details:\n  {log_dir}\n\n\
If this keeps happening, you can report it on our issue tracker and attach the log files."
    );

    let report = app
        .dialog()
        .message(message)
        .title("Geti stopped unexpectedly")
        .kind(MessageDialogKind::Error)
        .buttons(MessageDialogButtons::OkCancelCustom(
            "Report issue".to_string(),
            "Close".to_string(),
        ))
        .blocking_show();

    if report {
        open_issue_tracker(app);
    }
}

/// Wait for the backend to exit and react to unsolicited terminations. Runs on a
/// dedicated thread so it can block on `child.wait()` and call the *blocking*
/// dialog API (which must not run on the main thread).
fn monitor_backend(app: AppHandle, mut child: Child, control: BackendControl) {
    // Blocks until the backend exits (and reaps it, avoiding a zombie).
    let status = child.wait();

    // A deliberate shutdown (window closed / app quit) already killed it — the
    // exit is expected, so stay silent.
    if control.shutting_down.load(Ordering::SeqCst) {
        return;
    }

    let code = status.ok().and_then(|s| s.code());
    log::warn!("Backend exited unexpectedly (code {code:?})");

    match code {
        Some(MIGRATION_FATAL_EXIT_CODE) => {
            log::error!("Backend reported a fatal upgrade/migration failure (exit code 3)");
            // The backend drops a status file into DATA_DIR (== app_local_data_dir)
            // describing the failure and, crucially, where the pre-migration backup
            // lives. Read it so the dialog can show the user the exact path.
            let status = read_and_clear_fatal_status(&app);
            show_migration_failure_dialog(&app, status.as_ref());
            app.exit(MIGRATION_FATAL_EXIT_CODE);
        }
        other => {
            show_backend_crash_dialog(&app, other);
            app.exit(other.unwrap_or(1));
        }
    }
}

fn main() {
    let control = BackendControl::default();

    let app = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_log::Builder::default().build())
        .setup({
            let control = control.clone();
            move |app| {
                let child = spawn_backend(app.handle()).expect("Failed to spawn python backend");
                // Record the PID so shutdown can kill the whole tree, then hand
                // the child to a monitor thread that watches for crashes and
                // failed upgrades (exit code 3).
                *control.pid.lock().unwrap() = Some(child.id());
                let app_handle = app.handle().clone();
                let monitor_control = control.clone();
                std::thread::spawn(move || monitor_backend(app_handle, child, monitor_control));
                Ok(())
            }
        })
        // Geti is a single-window utility app, so closing the main window
        // should quit the whole process (default macOS behaviour is to keep
        // the app alive in the dock, which leaks the backend side-car).
        .on_window_event({
            let control = control.clone();
            move |window, event| {
                if let WindowEvent::CloseRequested { api, .. } = event {
                    // Prevent the default close so we can shut down gracefully.
                    // Destroying the window first lets the WebView2 / Chromium
                    // widget tear down cleanly before the process exits,
                    // avoiding the "Failed to unregister class
                    // Chrome_WidgetWin_0" error on Windows.
                    api.prevent_close();

                    // Kill the backend *before* exiting so worker processes
                    // cannot outlive the UI — even if RunEvent::Exit is
                    // short-circuited by exit(0).
                    shutdown_backend(&control);

                    let handle = window.app_handle().clone();
                    if let Err(e) = window.destroy() {
                        log::warn!("Failed to destroy window during shutdown: {e}");
                    }
                    handle.exit(0);
                }
            }
        })
        .invoke_handler(tauri::generate_handler![])
        .build(tauri::generate_context!())
        .expect("error building Tauri");

    // Belt-and-suspenders: also handle RunEvent::Exit for cases where the app
    // exits without going through the CloseRequested path (e.g. Cmd+Q on
    // macOS, or programmatic shutdown).
    let exit_control = control.clone();
    app.run(move |_app_handle, event| {
        if let RunEvent::Exit = event {
            shutdown_backend(&exit_control);
        }
    });
}
