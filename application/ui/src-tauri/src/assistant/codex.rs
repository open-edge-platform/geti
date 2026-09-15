//! Desktop-only bridge to the locally installed ChatGPT/Codex app.
//!
//! Instead of an API key, this path reuses the user's ChatGPT subscription by
//! driving `codex app-server` over stdio JSON-RPC. A fresh private subprocess
//! is spawned per operation: no socket is opened, no arbitrary RPC method is
//! exposed to the webview, and the subprocess runs with its own tools
//! (shell, filesystem, network, web search) disabled. The model's output is a
//! *proposal* — the host still validates and executes any Geti tool call
//! itself, exactly like in the API path.

use std::collections::{HashMap, HashSet};
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::sync::{Mutex, OnceLock};
use std::time::Duration;

use serde_json::{json, Value};
use tauri::ipc::Channel;
use tauri::{AppHandle, Manager, State};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::{ChildStdin, Command};
use tokio::sync::watch;

use crate::MAIN_WINDOW_LABEL;

/// Operations that talk to an account (login) or run a model need a lot longer
/// than the bookkeeping ones.
const SHORT_TIMEOUT: Duration = Duration::from_secs(30);
const LONG_TIMEOUT: Duration = Duration::from_secs(300);
const MAX_RESPONSE_BYTES: usize = 16 * 1024 * 1024;
const MAX_MODELS: usize = 1000;
const MAX_EARLY_CANCELS: usize = 64;
const MAX_TRACE_LINES: usize = 400;
const MAX_TRACE_LINE_CHARS: usize = 400;
const MAX_DETAIL_CHARS: usize = 200;
const VERSION_TIMEOUT: Duration = Duration::from_secs(10);

const CANCELLED: &str = "The ChatGPT request was cancelled.";

/// Guard rail sent to Codex on every turn. The assistant may only answer and
/// propose Geti tool calls; anything else it might be able to do locally is
/// off limits.
const DEVELOPER_INSTRUCTIONS: &str = concat!(
    "You are the assistant embedded in the Intel Geti desktop application. ",
    "Do not use shell, filesystem, network, plugin or other built-in tools. ",
    "Return only the requested JSON. The host validates and executes any proposed application ",
    "call itself and reports the result back to you."
);

#[derive(Default)]
pub struct CodexState {
    jobs: Mutex<HashMap<String, watch::Sender<bool>>>,
    /// Cancellations that arrived before the operation registered itself.
    early_cancels: Mutex<HashSet<String>>,
}

/// Shape Codex must answer in, so the host can parse a turn without guessing.
/// `calls` mirrors the Responses API `function_call` items.
fn output_schema() -> Value {
    json!({
        "type": "object",
        "additionalProperties": false,
        "required": ["text", "calls"],
        "properties": {
            "text": { "type": "string" },
            "calls": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": false,
                    "required": ["name", "arguments"],
                    "properties": {
                        "name": { "type": "string" },
                        "arguments": { "type": "string" }
                    }
                }
            }
        }
    })
}

/// Every place an official installer may leave the Codex CLI, in the order they
/// are tried. GUI launches do not reliably inherit the terminal's `PATH`, so
/// the well-known locations are probed before falling back to a bare command
/// name; the explicit executable setting always wins over all of them.
fn candidate_binaries() -> Vec<PathBuf> {
    let mut candidates: Vec<PathBuf> = Vec::new();

    #[cfg(windows)]
    {
        // `%LOCALAPPDATA%\OpenAI\Codex\bin\<version>\codex.exe` - the ChatGPT
        // app installer keeps one directory per version, so take the newest.
        if let Some(local) = std::env::var_os("LOCALAPPDATA") {
            let local = PathBuf::from(local);
            let versioned = local.join("OpenAI").join("Codex").join("bin");

            if let Ok(entries) = std::fs::read_dir(&versioned) {
                let mut binaries: Vec<PathBuf> = entries
                    .flatten()
                    .map(|entry| entry.path().join("codex.exe"))
                    .filter(|path| path.is_file())
                    .collect();

                binaries.sort_by_key(|path| path.metadata().and_then(|info| info.modified()).ok());
                candidates.extend(binaries.into_iter().rev());
            }

            candidates.push(versioned.join("codex.exe"));
            candidates.push(local.join("OpenAI").join("Codex").join("codex.exe"));
            candidates.push(local.join("Programs").join("ChatGPT").join("codex.exe"));
            candidates.push(
                local
                    .join("Programs")
                    .join("ChatGPT")
                    .join("resources")
                    .join("codex.exe"),
            );
            candidates.push(local.join("Programs").join("Codex").join("codex.exe"));
            // winget and Microsoft Store packages expose a shim here.
            candidates.push(
                local
                    .join("Microsoft")
                    .join("WinGet")
                    .join("Links")
                    .join("codex.exe"),
            );
        }

        // `npm i -g @openai/codex` only writes shims; the `.cmd` one is what a
        // shell resolves, and it needs `cmd.exe` to run.
        if let Some(appdata) = std::env::var_os("APPDATA") {
            let npm = PathBuf::from(appdata).join("npm");
            candidates.push(npm.join("codex.exe"));
            candidates.push(npm.join("codex.cmd"));
        }

        if let Some(files) = std::env::var_os("ProgramFiles") {
            let files = PathBuf::from(files);
            candidates.push(files.join("ChatGPT").join("codex.exe"));
            candidates.push(files.join("Codex").join("codex.exe"));
            candidates.push(files.join("nodejs").join("codex.cmd"));
        }

        if let Some(home) = home_dir() {
            candidates.push(home.join(".codex").join("bin").join("codex.exe"));
            candidates.push(home.join(".cargo").join("bin").join("codex.exe"));
            candidates.push(home.join("scoop").join("shims").join("codex.exe"));
            candidates.push(home.join("scoop").join("shims").join("codex.cmd"));
            candidates.push(home.join(".bun").join("bin").join("codex.exe"));
        }
    }

    #[cfg(target_os = "macos")]
    {
        candidates.push(PathBuf::from(
            "/Applications/ChatGPT.app/Contents/Resources/codex",
        ));
        candidates.push(PathBuf::from(
            "/Applications/Codex.app/Contents/Resources/codex",
        ));
        candidates.push(PathBuf::from("/opt/homebrew/bin/codex"));
        candidates.push(PathBuf::from("/usr/local/bin/codex"));
    }

    #[cfg(unix)]
    if let Some(home) = home_dir() {
        candidates.push(home.join(".codex").join("bin").join("codex"));
        candidates.push(home.join(".cargo").join("bin").join("codex"));
        candidates.push(home.join(".local").join("bin").join("codex"));
        candidates.push(home.join(".bun").join("bin").join("codex"));
        candidates.push(home.join(".npm-global").join("bin").join("codex"));
    }

    #[cfg(all(unix, not(target_os = "macos")))]
    {
        candidates.push(PathBuf::from("/usr/local/bin/codex"));
        candidates.push(PathBuf::from("/usr/bin/codex"));
        candidates.push(PathBuf::from("/snap/bin/codex"));
    }

    candidates
}

fn home_dir() -> Option<PathBuf> {
    std::env::var_os(if cfg!(windows) { "USERPROFILE" } else { "HOME" }).map(PathBuf::from)
}

/// Picks the first existing candidate, or `None` when only a bare `PATH`
/// lookup is left to try.
fn discover_binary() -> Option<PathBuf> {
    candidate_binaries().into_iter().find(|path| path.is_file())
}

fn default_binary() -> PathBuf {
    discover_binary().unwrap_or_else(|| PathBuf::from(if cfg!(windows) { "codex.exe" } else { "codex" }))
}

fn is_batch_shim(binary: &std::path::Path) -> bool {
    binary
        .extension()
        .and_then(|extension| extension.to_str())
        .is_some_and(|extension| extension.eq_ignore_ascii_case("cmd") || extension.eq_ignore_ascii_case("bat"))
}

/// Names a couple of the places that were checked, so the user can tell an
/// unusual install location apart from a missing install.
fn not_found_message() -> String {
    let searched: Vec<String> = candidate_binaries()
        .iter()
        .filter_map(|path| path.parent().map(|parent| parent.to_string_lossy().into_owned()))
        .take(4)
        .collect();

    format!(
        "Codex was not found. Install the ChatGPT/Codex app or run `npm i -g @openai/codex`, \
         or set the executable path in the settings. Looked in: {}.",
        searched.join(", ")
    )
}

/// Reports where Codex was found, and everywhere that was looked at, so the
/// settings can tell the user exactly what to fix.
#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CodexLocation {
    path: Option<String>,
    searched: Vec<String>,
}

#[tauri::command]
pub fn codex_locate() -> CodexLocation {
    CodexLocation {
        path: discover_binary().map(|path| path.to_string_lossy().into_owned()),
        searched: candidate_binaries()
            .iter()
            .map(|path| path.to_string_lossy().into_owned())
            .collect(),
    }
}

fn resolve_binary(executable: Option<String>) -> Result<PathBuf, String> {
    match executable.filter(|path| !path.trim().is_empty()) {
        Some(path) => {
            let path = PathBuf::from(path);
            if !path.is_absolute() || !path.is_file() {
                return Err("Choose the absolute path to the Codex executable.".to_string());
            }
            Ok(path)
        }
        None => Ok(default_binary()),
    }
}

/// Spawns Codex the way this host has to on each platform, with no console
/// window and through `cmd.exe` when the install is only a batch shim.
fn codex_command(binary: &Path) -> Command {
    let mut command = if is_batch_shim(binary) {
        // `CreateProcess` cannot execute a `.cmd`, which is all that
        // `npm i -g @openai/codex` installs on Windows.
        let mut command = Command::new("cmd.exe");
        command.arg("/C").arg(binary);
        command
    } else {
        Command::new(binary)
    };

    #[cfg(windows)]
    command.creation_flags(0x0800_0000); // CREATE_NO_WINDOW

    command
}

/// Protocol summary of the most recent operation. Login failures are only
/// visible in the traffic between the host and `codex app-server`, so the last
/// run is kept in memory and handed out by [`codex_diagnostics`].
fn trace_store() -> &'static Mutex<Vec<String>> {
    static TRACE: OnceLock<Mutex<Vec<String>>> = OnceLock::new();

    TRACE.get_or_init(|| Mutex::new(Vec::new()))
}

fn trace(line: impl Into<String>) {
    let Ok(mut lines) = trace_store().lock() else {
        return;
    };

    if lines.len() >= MAX_TRACE_LINES {
        lines.remove(0);
    }
    lines.push(truncate(&redact(&line.into()), MAX_TRACE_LINE_CHARS));
}

fn trace_reset() {
    if let Ok(mut lines) = trace_store().lock() {
        lines.clear();
    }
}

/// Tokens only ever reach this module inside URLs, so every query string is
/// dropped before a line is stored.
fn redact(line: &str) -> String {
    let mut out = String::with_capacity(line.len());
    let mut rest = line;

    while let Some(start) = rest.find("http") {
        let (head, tail) = rest.split_at(start);
        out.push_str(head);

        let end = tail
            .find(|character: char| character.is_whitespace() || character == '"')
            .unwrap_or(tail.len());
        let (url, after) = tail.split_at(end);

        match url.find('?') {
            Some(cut) => {
                out.push_str(&url[..cut]);
                out.push_str("?<redacted>");
            }
            None => out.push_str(url),
        }

        rest = after;
    }

    out.push_str(rest);
    out
}

fn truncate(text: &str, limit: usize) -> String {
    match text.char_indices().nth(limit) {
        Some((cut, _)) => format!("{}…", &text[..cut]),
        None => text.to_string(),
    }
}

/// Turns a JSON-RPC error object into a short, credential-free sentence.
fn describe_error(error: &Value) -> String {
    let code = error["code"].as_i64().unwrap_or(0);
    let message = error["message"].as_str().unwrap_or("no message");

    truncate(&redact(&format!("code {code}: {message}")), MAX_DETAIL_CHARS)
}

/// Records what came back without ever storing a payload: only the envelope,
/// the error detail and the key names of the result.
fn summarize(value: &Value) -> String {
    let mut parts: Vec<String> = Vec::new();

    if let Some(id) = value.get("id") {
        parts.push(format!("id={id}"));
    }
    if let Some(method) = value["method"].as_str() {
        parts.push(format!("method={method}"));
    }
    if let Some(error) = value.get("error") {
        parts.push(format!("error=({})", describe_error(error)));
    }
    if let Some(keys) = key_names(value.get("result")) {
        parts.push(format!("result={{{keys}}}"));
    }
    if let Some(keys) = key_names(value.get("params")) {
        parts.push(format!("params={{{keys}}}"));
    }

    if parts.is_empty() {
        "unrecognised message".to_string()
    } else {
        parts.join(" ")
    }
}

fn key_names(value: Option<&Value>) -> Option<String> {
    let value = value?;

    match value.as_object() {
        Some(map) => Some(map.keys().cloned().collect::<Vec<_>>().join(", ")),
        None => Some(truncate(&value.to_string(), 60)),
    }
}

async fn codex_version(binary: &Path) -> String {
    let probe = codex_command(binary)
        .arg("--version")
        .stdin(Stdio::null())
        .kill_on_drop(true)
        .output();

    match tokio::time::timeout(VERSION_TIMEOUT, probe).await {
        Ok(Ok(output)) => {
            let text = format!(
                "{}{}",
                String::from_utf8_lossy(&output.stdout),
                String::from_utf8_lossy(&output.stderr)
            );
            let text = text.trim();
            if text.is_empty() {
                format!("exited with {} and printed nothing", output.status)
            } else {
                truncate(&redact(text), MAX_DETAIL_CHARS)
            }
        }
        Ok(Err(error)) => format!("could not be started ({})", error.kind()),
        Err(_) => "timed out".to_string(),
    }
}

fn auth_state(home: &Path) -> &'static str {
    if home.join("auth.json").is_file() {
        "signed in (auth.json present)"
    } else if home.is_dir() {
        "signed out (no auth.json)"
    } else {
        "never used (directory missing)"
    }
}

/// Plain-text report the user can copy out of the settings when sign-in fails.
#[tauri::command]
pub async fn codex_diagnostics(app: AppHandle, executable: Option<String>) -> Result<String, String> {
    let mut report: Vec<String> = vec![
        "Geti assistant - ChatGPT diagnostics".to_string(),
        format!("platform: {} {}", std::env::consts::OS, std::env::consts::ARCH),
        format!(
            "executable setting: {}",
            executable.clone().filter(|path| !path.trim().is_empty()).unwrap_or_else(|| "(not set)".to_string())
        ),
    ];

    match resolve_binary(executable) {
        Ok(binary) => {
            report.push(format!(
                "resolved executable: {} (exists: {}, batch shim: {})",
                binary.display(),
                binary.is_file(),
                is_batch_shim(&binary)
            ));
            report.push(format!("codex --version: {}", codex_version(&binary).await));
        }
        Err(error) => report.push(format!("resolved executable: {error}")),
    }

    match app.path().app_data_dir() {
        Ok(dir) => {
            let home = dir.join("assistant-codex");
            report.push(format!("CODEX_HOME used by Geti: {} - {}", home.display(), auth_state(&home)));
        }
        Err(_) => report.push("CODEX_HOME used by Geti: unavailable".to_string()),
    }

    if let Some(home) = home_dir() {
        let shared = home.join(".codex");
        report.push(format!(
            "CODEX_HOME used by the ChatGPT app: {} - {}",
            shared.display(),
            auth_state(&shared)
        ));
    }

    report.push("searched locations:".to_string());
    report.extend(candidate_binaries().iter().map(|path| {
        format!(
            "  [{}] {}",
            if path.is_file() { "x" } else { " " },
            path.display()
        )
    }));

    report.push("last operation:".to_string());
    match trace_store().lock() {
        Ok(lines) if lines.is_empty() => report.push("  (nothing recorded yet - try signing in first)".to_string()),
        Ok(lines) => report.extend(lines.iter().map(|line| format!("  {line}"))),
        Err(_) => report.push("  unavailable".to_string()),
    }

    Ok(report.join("\n"))
}

async fn send(stdin: &mut ChildStdin, value: Value) -> Result<(), String> {
    trace(format!("-> {}", summarize(&value)));

    stdin
        .write_all(format!("{value}\n").as_bytes())
        .await
        .map_err(|_| "The ChatGPT connection closed.".to_string())
}

#[tauri::command]
pub fn codex_cancel(request_id: String, state: State<'_, CodexState>) -> Result<(), String> {
    let jobs = state
        .jobs
        .lock()
        .map_err(|_| "ChatGPT state unavailable".to_string())?;

    if let Some(sender) = jobs.get(&request_id) {
        let _ = sender.send(true);
        return Ok(());
    }

    let mut early = state
        .early_cancels
        .lock()
        .map_err(|_| "ChatGPT state unavailable".to_string())?;
    if early.len() >= MAX_EARLY_CANCELS {
        early.clear();
    }
    early.insert(request_id);

    Ok(())
}

#[tauri::command]
pub async fn codex_operation(
    app: AppHandle,
    request_id: String,
    operation: String,
    executable: Option<String>,
    body: Option<Value>,
    on_event: Channel<Value>,
    state: State<'_, CodexState>,
) -> Result<Value, String> {
    if !matches!(
        operation.as_str(),
        "status" | "login" | "logout" | "models" | "response"
    ) {
        return Err("Unsupported ChatGPT operation.".to_string());
    }

    let (cancel, mut cancelled) = watch::channel(false);
    {
        let mut jobs = state
            .jobs
            .lock()
            .map_err(|_| "ChatGPT state unavailable".to_string())?;

        let was_cancelled = state
            .early_cancels
            .lock()
            .map_err(|_| "ChatGPT state unavailable".to_string())?
            .remove(&request_id);
        if was_cancelled {
            return Err(CANCELLED.to_string());
        }

        // One subprocess at a time: a second `codex app-server` would race the
        // first over the same `CODEX_HOME` credential store.
        if !jobs.is_empty() {
            return Err("A ChatGPT operation is already running.".to_string());
        }
        jobs.insert(request_id.clone(), cancel);
    }

    let timeout = match operation.as_str() {
        "login" | "response" => LONG_TIMEOUT,
        _ => SHORT_TIMEOUT,
    };

    let outcome = tokio::select! {
        result = tokio::time::timeout(
            timeout,
            run(&app, &operation, executable, body.unwrap_or(Value::Null), on_event),
        ) => result.unwrap_or_else(|_| Err("The ChatGPT operation timed out.".to_string())),
        _ = cancelled.changed() => Err(CANCELLED.to_string()),
    };

    if let Ok(mut jobs) = state.jobs.lock() {
        jobs.remove(&request_id);
    }

    outcome
}

async fn run(
    app: &AppHandle,
    operation: &str,
    executable: Option<String>,
    body: Value,
    events: Channel<Value>,
) -> Result<Value, String> {
    let home = app
        .path()
        .app_data_dir()
        .map_err(|_| "Application storage unavailable.".to_string())?
        .join("assistant-codex");
    let workspace = home.join("workspace");
    std::fs::create_dir_all(&workspace).map_err(|_| "Could not prepare ChatGPT storage.".to_string())?;

    let binary = resolve_binary(executable)?;

    trace_reset();
    trace(format!("operation: {operation}"));
    trace(format!(
        "executable: {} (batch shim: {})",
        binary.display(),
        is_batch_shim(&binary)
    ));
    trace(format!("CODEX_HOME: {} - {}", home.display(), auth_state(&home)));

    let mut command = codex_command(&binary);

    command
        .args([
            "app-server",
            "--listen",
            "stdio://",
            "-c",
            "features.shell_tool=false",
            "-c",
            "features.unified_exec=false",
            "-c",
            "features.code_mode=false",
            "-c",
            "features.code_mode_only=false",
            "-c",
            "web_search=\"disabled\"",
            "-c",
            "cli_auth_credentials_store=\"keyring\"",
            "-c",
            "analytics.enabled=false",
        ])
        .env("CODEX_HOME", &home)
        // Never let an ambient key silently turn the "ChatGPT account" mode
        // into a metered API call.
        .env_remove("OPENAI_API_KEY")
        .env_remove("CODEX_API_KEY")
        .env_remove("CODEX_ACCESS_TOKEN")
        .current_dir(&workspace)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        // Codex reports a bad argument, an unusable credential store or a
        // failed browser handshake here and nowhere else.
        .stderr(Stdio::piped())
        .kill_on_drop(true);

    let mut child = command.spawn().map_err(|error| {
        trace(format!("spawn failed: {}", error.kind()));

        match error.kind() {
            std::io::ErrorKind::NotFound => not_found_message(),
            std::io::ErrorKind::PermissionDenied => {
                "Permission to run Codex was denied. Check the executable permissions.".to_string()
            }
            _ => "Codex could not start. Check that the executable is compatible with this system.".to_string(),
        }
    })?;

    if let Some(stderr) = child.stderr.take() {
        tokio::spawn(async move {
            let mut lines = BufReader::new(stderr).lines();
            while let Ok(Some(line)) = lines.next_line().await {
                trace(format!("stderr: {line}"));
            }
        });
    }

    let mut stdin = child.stdin.take().ok_or("ChatGPT input unavailable.")?;
    let mut stdout = BufReader::new(child.stdout.take().ok_or("ChatGPT output unavailable.")?).lines();

    let result = exchange(
        app,
        operation,
        &body,
        &workspace,
        &events,
        &mut stdin,
        &mut stdout,
    )
    .await;

    if let Ok(Some(status)) = child.try_wait() {
        trace(format!("codex exited on its own with {status}"));
    }
    if let Err(error) = &result {
        trace(format!("failed: {error}"));
    }

    let _ = child.kill().await;
    let _ = child.wait().await;

    result
}

async fn exchange(
    app: &AppHandle,
    operation: &str,
    body: &Value,
    workspace: &PathBuf,
    events: &Channel<Value>,
    stdin: &mut ChildStdin,
    stdout: &mut tokio::io::Lines<BufReader<tokio::process::ChildStdout>>,
) -> Result<Value, String> {
    send(
        stdin,
        json!({
            "id": 1,
            "method": "initialize",
            "params": {
                "clientInfo": { "name": "geti", "title": "Geti assistant", "version": "1.0.0" },
                "capabilities": {}
            }
        }),
    )
    .await?;

    let mut answer = String::new();
    let mut received = 0usize;
    let mut models: Vec<Value> = Vec::new();
    let mut cursors: HashSet<String> = HashSet::new();

    while let Some(line) = stdout
        .next_line()
        .await
        .map_err(|_| "The ChatGPT connection failed.".to_string())?
    {
        received += line.len();
        if received > MAX_RESPONSE_BYTES {
            return Err("The ChatGPT response exceeded the size limit.".to_string());
        }

        let value: Value = serde_json::from_str(&line).map_err(|error| {
            trace(format!("<- unparsable line: {error}"));
            "Invalid ChatGPT response.".to_string()
        })?;

        // Deltas would flood the diagnostics buffer and carry no protocol detail.
        if value["method"] != "item/agentMessage/delta" {
            trace(format!("<- {}", summarize(&value)));
        }

        // Upstream errors can echo request contents or credentials, so only the
        // redacted code and message are forwarded.
        if value.get("error").is_some() && value.get("id").is_some() {
            return Err(format!(
                "ChatGPT rejected the request ({}). Check the installed Codex version, account access \
                 and model availability.",
                describe_error(&value["error"])
            ));
        }

        if value["id"] == 1 {
            send(stdin, json!({ "method": "initialized", "params": {} })).await?;

            let request = match operation {
                "login" => json!({ "method": "account/login/start", "params": { "type": "chatgpt" } }),
                "logout" => json!({ "method": "account/logout", "params": {} }),
                "models" => json!({
                    "method": "model/list",
                    "params": { "limit": 100, "includeHidden": false }
                }),
                "response" => json!({
                    "method": "thread/start",
                    "params": {
                        "model": body["model"],
                        "cwd": workspace,
                        "approvalPolicy": "never",
                        "sandbox": "read-only",
                        "ephemeral": true,
                        "baseInstructions": body["instructions"],
                        "developerInstructions": DEVELOPER_INSTRUCTIONS
                    }
                }),
                _ => json!({ "method": "account/read", "params": { "refreshToken": false } }),
            };

            send(
                stdin,
                json!({ "id": 2, "method": request["method"], "params": request["params"] }),
            )
            .await?;
        } else if value["id"] == 2 {
            match operation {
                "models" => {
                    let page = value["result"]["data"]
                        .as_array()
                        .ok_or("Invalid ChatGPT model list.")?;
                    models.extend(page.iter().cloned());
                    if models.len() > MAX_MODELS {
                        return Err("The ChatGPT model list exceeded the size limit.".to_string());
                    }

                    match value["result"]["nextCursor"].as_str() {
                        Some(cursor) => {
                            if !cursors.insert(cursor.to_string()) {
                                return Err("Invalid ChatGPT model pagination.".to_string());
                            }
                            send(
                                stdin,
                                json!({
                                    "id": 2,
                                    "method": "model/list",
                                    "params": { "limit": 100, "includeHidden": false, "cursor": cursor }
                                }),
                            )
                            .await?;
                        }
                        None => return Ok(json!({ "data": models })),
                    }
                }
                "login" => {
                    let url = value["result"]["authUrl"].as_str().ok_or_else(|| {
                        format!(
                            "ChatGPT did not return a login URL. It answered with {}.",
                            key_names(value.get("result")).unwrap_or_else(|| "nothing".to_string())
                        )
                    })?;
                    if !url.starts_with("https://auth.openai.com/") && !url.starts_with("https://chatgpt.com/") {
                        return Err("Invalid ChatGPT login URL.".to_string());
                    }
                    events
                        .send(json!({ "type": "login", "url": url }))
                        .map_err(|_| "The login view was closed.".to_string())?;
                }
                "response" => {
                    let thread = value["result"]["thread"]["id"]
                        .as_str()
                        .ok_or("ChatGPT did not create a conversation.")?;
                    let input = build_turn_input(body);

                    send(
                        stdin,
                        json!({
                            "id": 3,
                            "method": "turn/start",
                            "params": {
                                "threadId": thread,
                                "input": input,
                                "outputSchema": output_schema(),
                                "approvalPolicy": "never"
                            }
                        }),
                    )
                    .await?;
                }
                _ => return Ok(value["result"].clone()),
            }
        } else if value["method"] == "account/login/completed" && operation == "login" {
            if value["params"]["success"] == true {
                // The browser took focus for the sign-in; bring the app back so
                // the user sees the connected state.
                if let Some(window) = app.get_webview_window(MAIN_WINDOW_LABEL) {
                    let _ = window.unminimize();
                    let _ = window.set_focus();
                }
                return Ok(json!({ "connected": true }));
            }
            return Err(match value["params"]["error"].as_str() {
                Some(detail) => format!(
                    "The ChatGPT login was not completed: {}",
                    truncate(&redact(detail), MAX_DETAIL_CHARS)
                ),
                None => "The ChatGPT login was not completed.".to_string(),
            });
        } else if value["method"] == "item/agentMessage/delta" {
            if let Some(delta) = value["params"]["delta"].as_str() {
                answer.push_str(delta);
            }
        } else if value["method"] == "item/completed" && value["params"]["item"]["type"] == "agentMessage" {
            if let Some(text) = value["params"]["item"]["text"].as_str() {
                answer = text.to_string();
            }
        } else if value["method"] == "turn/completed" {
            if value["params"]["turn"]["status"] != "completed" {
                return Err(
                    "ChatGPT could not complete the turn. Check your ChatGPT usage limits and model access."
                        .to_string(),
                );
            }
            return serde_json::from_str(&answer)
                .map_err(|_| "ChatGPT returned a malformed response.".to_string());
        } else if value.get("method").is_some() && value.get("id").is_some() {
            // Deny every server-initiated tool/approval request: this adapter
            // only consumes structured output.
            send(
                stdin,
                json!({
                    "id": value["id"],
                    "error": { "code": -32601, "message": "Unavailable in the Geti assistant" }
                }),
            )
            .await?;
        }
    }

    Err("ChatGPT closed before completing the request. Open the diagnostics report in the settings to see what \
         Codex reported."
        .to_string())
}

/// Flattens a Responses-API style transcript into a single Codex turn.
///
/// Codex takes images as separate `image` input parts, so inline
/// `input_image` items are lifted out of the transcript and replaced with a
/// placeholder before the transcript is handed over as text.
fn build_turn_input(body: &Value) -> Vec<Value> {
    let mut input = Vec::new();
    let mut transcript = body["input"].clone();

    if let Some(items) = transcript.as_array_mut() {
        for item in items {
            if let Some(content) = item["content"].as_array_mut() {
                for part in content.iter_mut() {
                    if part["type"] == "input_image" {
                        input.push(json!({ "type": "image", "url": part["image_url"] }));
                        *part = json!({ "type": "input_text", "text": "[Attached image]" });
                    }
                }
            }
        }
    }

    input.push(json!({
        "type": "text",
        "text": format!(
            "Continue this conversation. Available application tools: {}\nConversation: {}\n\
             Return {{text, calls}}. Each call has a name and arguments (a JSON-encoded string). \
             Use an empty calls array for a final answer. Never claim a tool succeeded without its result.",
            body["tools"], transcript
        )
    }));

    input
}
