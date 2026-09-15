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
use std::path::PathBuf;
use std::process::Stdio;
use std::sync::Mutex;
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

/// GUI launches do not inherit the terminal's `PATH`, so look in the places the
/// official installers use before falling back to a bare command name. The
/// explicit executable setting stays available for portable installs.
fn default_binary() -> PathBuf {
    #[cfg(windows)]
    if let Some(local) = std::env::var_os("LOCALAPPDATA") {
        let directory = PathBuf::from(local).join("OpenAI").join("Codex").join("bin");
        if let Ok(entries) = std::fs::read_dir(directory) {
            let mut binaries: Vec<PathBuf> = entries
                .flatten()
                .map(|entry| entry.path().join("codex.exe"))
                .filter(|path| path.is_file())
                .collect();
            binaries.sort_by_key(|path| path.metadata().and_then(|info| info.modified()).ok());
            if let Some(binary) = binaries.pop() {
                return binary;
            }
        }
    }

    #[cfg(target_os = "macos")]
    for location in [
        "/Applications/Codex.app/Contents/Resources/codex",
        "/Applications/ChatGPT.app/Contents/Resources/codex",
        "/opt/homebrew/bin/codex",
        "/usr/local/bin/codex",
    ] {
        let binary = PathBuf::from(location);
        if binary.is_file() {
            return binary;
        }
    }

    PathBuf::from(if cfg!(windows) { "codex.exe" } else { "codex" })
}

async fn send(stdin: &mut ChildStdin, value: Value) -> Result<(), String> {
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

    let binary = match executable.filter(|path| !path.trim().is_empty()) {
        Some(path) => {
            let path = PathBuf::from(path);
            if !path.is_absolute() || !path.is_file() {
                return Err("Choose the absolute path to the Codex executable.".to_string());
            }
            path
        }
        None => default_binary(),
    };

    let mut command = Command::new(binary);
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
        .stderr(Stdio::null())
        .kill_on_drop(true);

    #[cfg(windows)]
    command.creation_flags(0x0800_0000); // CREATE_NO_WINDOW

    let mut child = command.spawn().map_err(|error| match error.kind() {
        std::io::ErrorKind::NotFound => {
            "Codex was not found. Install the ChatGPT/Codex app, or enter the path to its executable."
        }
        std::io::ErrorKind::PermissionDenied => {
            "Permission to run Codex was denied. Check the executable permissions."
        }
        _ => "Codex could not start. Check that the executable is compatible with this system.",
    })?;

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

        let value: Value = serde_json::from_str(&line).map_err(|_| "Invalid ChatGPT response.".to_string())?;

        // Upstream errors can echo request contents or credentials, so they are
        // never forwarded verbatim.
        if value.get("error").is_some() && value.get("id").is_some() {
            return Err(
                "ChatGPT rejected the request. Check the installed Codex version, account access and model availability."
                    .to_string(),
            );
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
                    let url = value["result"]["authUrl"]
                        .as_str()
                        .ok_or("ChatGPT did not return a login URL.")?;
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
            return Err("The ChatGPT login was not completed.".to_string());
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

    Err("ChatGPT closed before completing the request.".to_string())
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
