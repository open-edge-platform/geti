// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

use std::collections::{HashMap, HashSet};
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::sync::Mutex;
use std::time::Duration;

use serde::Serialize;
use serde_json::{json, Value};
use tauri::ipc::Channel;
use tauri::{AppHandle, Manager, State};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::{ChildStdin, Command};
use tokio::sync::watch;

use crate::MAIN_WINDOW_LABEL;

const SHORT_TIMEOUT: Duration = Duration::from_secs(30);
const LONG_TIMEOUT: Duration = Duration::from_secs(300);
const MAX_RESPONSE_BYTES: usize = 16 * 1024 * 1024;
const MAX_MODELS: usize = 1000;

const DEVELOPER_INSTRUCTIONS: &str = concat!(
    "You are the annotation assistant embedded in Intel Geti. ",
    "Do not use shell, filesystem, network, plugin, or other built-in tools. ",
    "Return only the requested JSON. The host validates and executes proposed application calls."
);

#[derive(Default)]
pub struct CodexState {
    jobs: Mutex<HashMap<String, watch::Sender<bool>>>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CodexLocation {
    path: Option<String>,
    searched: Vec<String>,
}

fn home_dir() -> Option<PathBuf> {
    std::env::var_os("USERPROFILE").map(PathBuf::from)
}

fn candidate_binaries() -> Vec<PathBuf> {
    let mut candidates = Vec::new();
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
        candidates.push(local.join("Microsoft").join("WinGet").join("Links").join("codex.exe"));
    }
    if let Some(appdata) = std::env::var_os("APPDATA") {
        let npm = PathBuf::from(appdata).join("npm");
        candidates.push(npm.join("codex.exe"));
        candidates.push(npm.join("codex.cmd"));
    }
    if let Some(home) = home_dir() {
        candidates.push(home.join(".codex").join("bin").join("codex.exe"));
        candidates.push(home.join(".cargo").join("bin").join("codex.exe"));
        candidates.push(home.join("scoop").join("shims").join("codex.exe"));
        candidates.push(home.join("scoop").join("shims").join("codex.cmd"));
    }
    candidates
}

fn discover_binary() -> Option<PathBuf> {
    candidate_binaries().into_iter().find(|path| path.is_file())
}

fn is_batch(binary: &Path) -> bool {
    binary
        .extension()
        .and_then(|extension| extension.to_str())
        .is_some_and(|extension| extension.eq_ignore_ascii_case("cmd") || extension.eq_ignore_ascii_case("bat"))
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
        None => Ok(discover_binary().unwrap_or_else(|| PathBuf::from("codex.exe"))),
    }
}

fn command(binary: &Path) -> Command {
    let mut command = if is_batch(binary) {
        let mut command = Command::new("cmd.exe");
        command.arg("/C").arg(binary);
        command
    } else {
        Command::new(binary)
    };
    command.creation_flags(0x0800_0000);
    command
}

fn not_found_message() -> String {
    let searched: Vec<String> = candidate_binaries()
        .iter()
        .filter_map(|path| path.parent().map(|parent| parent.to_string_lossy().into_owned()))
        .take(4)
        .collect();
    format!(
        "Codex was not found. Install ChatGPT/Codex or choose its executable. Looked in: {}.",
        searched.join(", ")
    )
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

#[tauri::command]
pub async fn codex_diagnostics(app: AppHandle, executable: Option<String>) -> Result<String, String> {
    let binary = resolve_binary(executable)?;
    let mut probe = command(&binary);
    probe
        .arg("--version")
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .kill_on_drop(true);
    let version = match tokio::time::timeout(Duration::from_secs(10), probe.output()).await {
        Ok(Ok(output)) => format!(
            "{}{}",
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr)
        )
        .trim()
        .to_string(),
        Ok(Err(error)) if error.kind() == std::io::ErrorKind::NotFound => not_found_message(),
        Ok(Err(error)) => format!("Codex could not start: {}", error.kind()),
        Err(_) => "Codex version check timed out.".to_string(),
    };
    let home = codex_home(&app)?;
    Ok(format!(
        "Geti ChatGPT diagnostics\nexecutable: {}\nversion: {}\nprofile: {}",
        binary.display(),
        version,
        home.display()
    ))
}

#[tauri::command]
pub fn codex_cancel(request_id: String, state: State<'_, CodexState>) -> Result<(), String> {
    let jobs = state
        .jobs
        .lock()
        .map_err(|_| "ChatGPT state unavailable.".to_string())?;
    if let Some(cancel) = jobs.get(&request_id) {
        let _ = cancel.send(true);
    }
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
    if !matches!(operation.as_str(), "status" | "login" | "logout" | "models" | "response") {
        return Err("Unsupported ChatGPT operation.".to_string());
    }
    let (cancel, mut cancelled) = watch::channel(false);
    {
        let mut jobs = state
            .jobs
            .lock()
            .map_err(|_| "ChatGPT state unavailable.".to_string())?;
        if !jobs.is_empty() {
            return Err("A ChatGPT operation is already running.".to_string());
        }
        jobs.insert(request_id.clone(), cancel);
    }
    let timeout = if matches!(operation.as_str(), "login" | "response") {
        LONG_TIMEOUT
    } else {
        SHORT_TIMEOUT
    };
    let outcome = tokio::select! {
        result = tokio::time::timeout(
            timeout,
            run(&app, &operation, executable, body.unwrap_or(Value::Null), on_event),
        ) => result.unwrap_or_else(|_| Err("The ChatGPT operation timed out.".to_string())),
        _ = cancelled.changed() => Err("Stopped.".to_string()),
    };
    if let Ok(mut jobs) = state.jobs.lock() {
        jobs.remove(&request_id);
    }
    outcome
}

fn codex_home(app: &AppHandle) -> Result<PathBuf, String> {
    let home = app
        .path()
        .app_data_dir()
        .map_err(|_| "Application storage unavailable.".to_string())?
        .join("assistant-codex");
    std::fs::create_dir_all(home.join("workspace"))
        .map_err(|error| format!("Could not prepare ChatGPT storage: {error}"))?;
    std::fs::canonicalize(home).map_err(|error| format!("Could not resolve ChatGPT storage: {error}"))
}

async fn run(
    app: &AppHandle,
    operation: &str,
    executable: Option<String>,
    body: Value,
    events: Channel<Value>,
) -> Result<Value, String> {
    let binary = resolve_binary(executable)?;
    let home = codex_home(app)?;
    let workspace = home.join("workspace");
    let mut process = command(&binary);
    process
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
        .env_remove("OPENAI_API_KEY")
        .env_remove("CODEX_API_KEY")
        .env_remove("CODEX_ACCESS_TOKEN")
        .current_dir(&workspace)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .kill_on_drop(true);
    let mut child = process.spawn().map_err(|error| match error.kind() {
        std::io::ErrorKind::NotFound => not_found_message(),
        std::io::ErrorKind::PermissionDenied => "Permission to run Codex was denied.".to_string(),
        _ => "Codex could not start.".to_string(),
    })?;
    let mut stdin = child.stdin.take().ok_or("ChatGPT input unavailable.")?;
    let mut stdout = BufReader::new(child.stdout.take().ok_or("ChatGPT output unavailable.")?).lines();
    let result = exchange(app, operation, &body, &workspace, &events, &mut stdin, &mut stdout).await;
    let _ = child.kill().await;
    let _ = child.wait().await;
    result
}

async fn send(stdin: &mut ChildStdin, value: Value) -> Result<(), String> {
    stdin
        .write_all(format!("{value}\n").as_bytes())
        .await
        .map_err(|_| "The ChatGPT connection closed.".to_string())
}

async fn exchange(
    app: &AppHandle,
    operation: &str,
    body: &Value,
    workspace: &Path,
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
    let mut models = Vec::new();
    let mut cursors = HashSet::new();
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
        if value.get("error").is_some() && value.get("id").is_some() {
            return Err("ChatGPT rejected the request. Check the installed Codex version and account access.".to_string());
        }
        if value["id"] == 1 {
            send(stdin, json!({ "method": "initialized", "params": {} })).await?;
            let request = match operation {
                "login" => json!({ "method": "account/login/start", "params": { "type": "chatgpt" } }),
                "logout" => json!({ "method": "account/logout", "params": {} }),
                "models" => json!({ "method": "model/list", "params": { "limit": 100, "includeHidden": false } }),
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
            send(stdin, json!({ "id": 2, "method": request["method"], "params": request["params"] })).await?;
        } else if value["id"] == 2 {
            match operation {
                "models" => {
                    let page = value["result"]["data"].as_array().ok_or("Invalid ChatGPT model list.")?;
                    models.extend(page.iter().cloned());
                    if models.len() > MAX_MODELS {
                        return Err("The ChatGPT model list exceeded the size limit.".to_string());
                    }
                    if let Some(cursor) = value["result"]["nextCursor"].as_str() {
                        if !cursors.insert(cursor.to_string()) {
                            return Err("Invalid ChatGPT model pagination.".to_string());
                        }
                        send(
                            stdin,
                            json!({ "id": 2, "method": "model/list", "params": {
                                "limit": 100, "includeHidden": false, "cursor": cursor
                            }}),
                        )
                        .await?;
                    } else {
                        return Ok(json!({ "data": models }));
                    }
                }
                "login" => {
                    let url = value["result"]["authUrl"].as_str().ok_or("ChatGPT did not return a login URL.")?;
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
                    send(
                        stdin,
                        json!({ "id": 3, "method": "turn/start", "params": {
                            "threadId": thread,
                            "input": build_turn_input(body),
                            "outputSchema": output_schema(),
                            "approvalPolicy": "never"
                        }}),
                    )
                    .await?;
                }
                _ => return Ok(value["result"].clone()),
            }
        } else if value["method"] == "account/login/completed" && operation == "login" {
            if value["params"]["success"] == true {
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
                return Err("ChatGPT could not complete the turn.".to_string());
            }
            return serde_json::from_str(&answer).map_err(|_| "ChatGPT returned a malformed response.".to_string());
        } else if value.get("method").is_some() && value.get("id").is_some() {
            send(
                stdin,
                json!({ "id": value["id"], "error": {
                    "code": -32601, "message": "Unavailable in the Geti assistant"
                }}),
            )
            .await?;
        }
    }
    Err("ChatGPT closed before completing the request.".to_string())
}

fn output_schema() -> Value {
    json!({
        "type": "object",
        "additionalProperties": false,
        "required": ["text", "calls"],
        "properties": {
            "text": { "type": "string" },
            "calls": { "type": "array", "items": {
                "type": "object",
                "additionalProperties": false,
                "required": ["name", "arguments"],
                "properties": { "name": { "type": "string" }, "arguments": { "type": "string" } }
            }}
        }
    })
}

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
    input.push(json!({ "type": "text", "text": format!(
        "Continue this conversation. Available application tools: {}\nConversation: {}\n\
         Return {{text, calls}}. Each call has a name and arguments as a JSON-encoded string. \
         Use an empty calls array for a final answer.",
        body["tools"], transcript
    ) }));
    input
}

#[cfg(test)]
mod tests {
    use super::{build_turn_input, output_schema};
    use serde_json::json;

    #[test]
    fn lifts_images_and_requires_structured_calls() {
        let body = json!({
            "input": [{ "type": "message", "role": "user", "content": [
                { "type": "input_image", "image_url": "data:image/png;base64,AA" }
            ]}],
            "tools": []
        });
        let input = build_turn_input(&body);
        assert_eq!(input[0]["type"], "image");
        assert_eq!(output_schema()["required"], json!(["text", "calls"]));
    }
}