// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod backend;

use std::fs::OpenOptions;
use std::io::Write as _;
use std::process::Child;
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex, OnceLock};
use std::time::{Instant, SystemTime, UNIX_EPOCH};

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

/// Per-user directory the **Windows** backend actually uses for both data and
/// logs.
///
/// The frozen Windows backend's PyInstaller runtime hook
/// (`application/backend/pyinstaller/windows/uwp.py`) unconditionally overrides
/// `DATA_DIR` *and* `LOG_DIR` to `%LOCALAPPDATA%\Intel\Geti`, ignoring whatever
/// the shell passed on the command line. If the shell resolved these paths from
/// Tauri's bundle identifier (`com.intel.geti`) instead, its dialogs would point
/// users at the wrong folder and `read_and_clear_fatal_status` would look for the
/// backend's status file in the wrong place. Keep this in sync with `uwp.py`.
#[cfg(windows)]
fn backend_app_data_dir() -> Option<PathBuf> {
    std::env::var_os("LOCALAPPDATA").map(|p| PathBuf::from(p).join("Intel").join("Geti"))
}

/// Resolve the directory the backend uses for persistent data, matching the
/// backend's own precedence: an explicit `DATA_DIR` override wins, then (on
/// Windows) the hard-coded `%LOCALAPPDATA%\Intel\Geti` from `uwp.py`, and finally
/// Tauri's identifier-derived `app_local_data_dir()`.
fn resolve_data_dir(app: &AppHandle) -> Option<PathBuf> {
    if let Some(dir) = std::env::var_os("DATA_DIR") {
        return Some(PathBuf::from(dir));
    }
    #[cfg(windows)]
    if let Some(dir) = backend_app_data_dir() {
        return Some(dir);
    }
    app.path().app_local_data_dir().ok()
}

/// Resolve the directory the backend writes logs to, mirroring [`resolve_data_dir`]
/// (on Windows `uwp.py` points `LOG_DIR` at the same `Intel\Geti` folder).
fn resolve_log_dir(app: &AppHandle) -> Option<PathBuf> {
    if let Some(dir) = std::env::var_os("LOG_DIR") {
        return Some(PathBuf::from(dir));
    }
    #[cfg(windows)]
    if let Some(dir) = backend_app_data_dir() {
        return Some(dir);
    }
    app.path().app_log_dir().ok()
}

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

/// Read and remove the backend's fatal-status file from the resolved data
/// directory (see [`resolve_data_dir`]).
///
/// Returns `None` if the file is absent or unreadable. The file is always
/// deleted after a successful read so a stale status can't resurface on the next
/// launch; the backend also clears it on a healthy start as a second safeguard.
fn read_and_clear_fatal_status(app: &AppHandle) -> Option<FatalStatus> {
    let path = resolve_data_dir(app)?.join(FATAL_STATUS_FILENAME);
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

// ---------------------------------------------------------------------------
// TEMPORARY shutdown instrumentation
//
// Measures how long each phase of the window-close path takes, so the ~8 s exit
// delay reported for the packaged Windows build can be attributed to a concrete
// step instead of guessed at. Every line goes to the normal Tauri log *and* to
// `<log dir>/shutdown-trace.log`, which is opened/flushed/closed per line so the
// data survives even if the process is killed or hangs mid-shutdown.
//
// Deliberately not gated on `debug_assertions`: the interesting costs (GUI
// subsystem => a fresh console + conhost for every child process, MSIX package
// identity) only exist in a real release build, so a debug build would hide
// them. Remove this block once the root cause is confirmed.
// ---------------------------------------------------------------------------

/// Instant the shell process started; zero point of every trace line.
static APP_START: OnceLock<Instant> = OnceLock::new();

/// Resolved trace-file path (`None` when no log directory could be resolved).
static TRACE_FILE: OnceLock<Option<PathBuf>> = OnceLock::new();

/// Wall-clock milliseconds since the Unix epoch, so trace lines can be lined up
/// with observations made outside the process (Task Manager, Process Monitor, a
/// PowerShell watcher polling for the PID to disappear).
fn epoch_millis() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0)
}

/// Append one instrumentation line, flushing immediately.
fn trace(msg: &str) {
    let elapsed = APP_START.get().map(|t| t.elapsed().as_millis()).unwrap_or(0);
    log::info!("[shutdown-trace +{elapsed} ms] {msg}");

    if let Some(Some(path)) = TRACE_FILE.get() {
        if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(path) {
            let _ = writeln!(file, "{}\t+{} ms\t{}", epoch_millis(), elapsed, msg);
            let _ = file.flush();
        }
    }
}

/// Run `f`, trace how long it took, and hand back its result.
fn trace_step<T>(label: &str, f: impl FnOnce() -> T) -> T {
    trace(&format!("-> {label}"));
    let start = Instant::now();
    let result = f();
    trace(&format!("<- {label} took {} ms", start.elapsed().as_millis()));
    result
}

/// Set up the trace sink. Must run before anything else in `setup()`.
fn init_trace(app: &AppHandle) {
    let _ = APP_START.set(Instant::now());

    let path = resolve_log_dir(app).map(|dir| {
        let _ = std::fs::create_dir_all(&dir);
        dir.join("shutdown-trace.log")
    });
    let _ = TRACE_FILE.set(path);

    let debug_build = cfg!(debug_assertions);
    trace(&format!(
        "=== app start: pid={} debug_assertions={debug_build} trace_file={:?}",
        std::process::id(),
        TRACE_FILE.get().and_then(|p| p.as_ref())
    ));
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
    /// TEMPORARY: instant the kill was issued, so the monitor thread can report
    /// how long the backend tree actually took to die.
    kill_started: Arc<Mutex<Option<Instant>>>,
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

        // TEMPORARY control probe. Spawning a trivial console child measures the
        // fixed cost of `CreateProcess` from *this* process — console + conhost
        // allocation in a GUI-subsystem build, plus MSIX AppModel overhead —
        // without doing any process-tree work. Subtracting it from the taskkill
        // timing below separates "starting any child process is slow here" from
        // "enumerating the process tree is slow".
        trace_step("probe: spawn `cmd /c exit`", || {
            let _ = Command::new("cmd").args(["/c", "exit"]).output();
        });

        let result = trace_step("taskkill /F /T", || {
            Command::new("taskkill")
                .args(["/F", "/T", "/PID", &pid.to_string()])
                .output()
        });

        // The stdout of `taskkill /T` lists every PID it terminated, which tells
        // us for free how large the backend process tree was.
        match result {
            Ok(output) => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                let stderr = String::from_utf8_lossy(&output.stderr);
                trace(&format!(
                    "taskkill exit={:?} stdout={:?} stderr={:?}",
                    output.status.code(),
                    stdout.trim(),
                    stderr.trim()
                ));
            }
            Err(e) => trace(&format!("taskkill could not be started: {e}")),
        }
    }

    #[cfg(unix)]
    {
        use std::process::Command;
        // kill -- -PID sends the signal to the whole process group.
        trace_step("kill -9 -- -<pid>", || {
            let _ = Command::new("kill")
                .args(["-9", "--", &format!("-{pid}")])
                .output();
        });
    }
}

/// Deliberately terminate the backend (app shutdown). Marks the exit as intended
/// so the monitor thread stays silent instead of showing a crash dialog.
fn shutdown_backend(control: &BackendControl) {
    control.shutting_down.store(true, Ordering::SeqCst);
    let pid = control.pid.lock().unwrap().take();
    match pid {
        Some(pid) => {
            *control.kill_started.lock().unwrap() = Some(Instant::now());
            trace_step(&format!("shutdown_backend(pid={pid})"), || {
                kill_process_tree(pid);
            });
            log::info!("⛔ Backend terminated");
        }
        None => trace("shutdown_backend: no PID recorded, backend already shut down"),
    }
}

/// Resolve the per-user log directory as a display string for user-facing
/// messages, falling back to a generic phrase if it can't be resolved.
fn log_dir_hint(app: &AppHandle) -> String {
    resolve_log_dir(app)
        .map(|p| p.display().to_string())
        .unwrap_or_else(|| "the application log directory".to_string())
}

/// Detailed message shown when the backend aborts an in-place upgrade because
/// the data migration failed (exit code 3). When the backend provided a
/// [`FatalStatus`] with a backup path, the exact recovery instructions are
/// included so the user can restore their data by hand if needed.
fn show_migration_failure_dialog(app: &AppHandle, status: Option<&FatalStatus>) {
    let log_dir = log_dir_hint(app);

    // Assemble the body from independent paragraphs and join them with a single
    // blank line. Building it this way (instead of interpolating optional
    // fragments into one big format string) guarantees no stray empty line is
    // left behind when the recovery paragraph is absent.
    let mut paragraphs: Vec<String> = vec![
        "Geti tried to upgrade your data to this newer version, but the upgrade did not \
succeed."
            .to_string(),
        "The newer version of Geti cannot run with your existing data and will now close."
            .to_string(),
    ];

    if let Some(backup_path) = status.and_then(|s| s.backup_path.as_deref()) {
        let db_target = status
            .and_then(|s| s.database_path.as_deref())
            .map(|db| format!("'{db}' (the original database file)"))
            .unwrap_or_else(|| "the original database file".to_string());
        paragraphs.push(format!(
            "To recover, restore the pre-migration database backup: rename the backup file \
'{backup_path}' back to {db_target}, overwriting the partially migrated database. After \
restoring the backup, downgrade the application to the previous version."
        ));
    }

    paragraphs.push(format!("Logs are available at:\n  {log_dir}"));
    paragraphs.push(
        "If the problem persists, you can report it on our issue tracker and attach the log \
files."
            .to_string(),
    );

    let message = paragraphs.join("\n\n");

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
        // TEMPORARY: how long the backend tree really took to disappear after
        // the kill was issued — `taskkill` returning is not the same as the
        // processes actually being gone.
        let waited = control
            .kill_started
            .lock()
            .unwrap()
            .map(|t| t.elapsed().as_millis());
        trace(&format!(
            "backend side-car reaped {waited:?} ms after the kill was issued (exit code {:?})",
            status.as_ref().ok().and_then(|s| s.code())
        ));
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
                init_trace(app.handle());
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
                    trace("WindowEvent::CloseRequested — shutdown starts here (T0)");

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
                    trace_step("window.destroy()", || {
                        if let Err(e) = window.destroy() {
                            log::warn!("Failed to destroy window during shutdown: {e}");
                        }
                    });
                    trace("calling AppHandle::exit(0)");
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
    app.run(move |_app_handle, event| match event {
        RunEvent::ExitRequested { .. } => trace("RunEvent::ExitRequested"),
        RunEvent::Exit => {
            shutdown_backend(&exit_control);
            // Last line we can emit from inside the process: everything after
            // this (WebView2 host/GPU/renderer teardown, unmapping the backend's
            // torch/OpenVINO address spaces, AV process-exit callbacks) is only
            // observable from outside.
            trace("RunEvent::Exit handled — OS/WebView2 teardown starts now");
        }
        _ => {}
    });
}
