// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::sync::Mutex;
use std::time::Duration;

use serde::Serialize;
use serde_json::{json, Value};
use tauri::{AppHandle, Manager, State};
use tokio::io::AsyncWriteExt;
use tokio::process::Command;
use tokio::sync::watch;

const SHORT_TIMEOUT: Duration = Duration::from_secs(30);
const LONG_TIMEOUT: Duration = Duration::from_secs(300);
const MAX_OUTPUT_BYTES: usize = 16 * 1024 * 1024;

#[derive(Default)]
pub struct ClaudeState {
    jobs: Mutex<HashMap<String, watch::Sender<bool>>>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ClaudeLocation {
    path: Option<String>,
    searched: Vec<String>,
}

fn candidate_binaries() -> Vec<PathBuf> {
    let mut candidates = Vec::new();
    if let Some(home) = std::env::var_os("USERPROFILE") {
        let home = PathBuf::from(home);
        candidates.push(home.join(".local").join("bin").join("claude.exe"));
        candidates.push(home.join(".claude").join("bin").join("claude.exe"));
        candidates.push(home.join("scoop").join("shims").join("claude.exe"));
        candidates.push(home.join("scoop").join("shims").join("claude.cmd"));
    }
    if let Some(local) = std::env::var_os("LOCALAPPDATA") {
        let local = PathBuf::from(local);
        candidates.push(local.join("Programs").join("Claude").join("claude.exe"));
        candidates.push(local.join("Microsoft").join("WinGet").join("Links").join("claude.exe"));
    }
    if let Some(appdata) = std::env::var_os("APPDATA") {
        let npm = PathBuf::from(appdata).join("npm");
        candidates.push(npm.join("claude.exe"));
        candidates.push(npm.join("claude.cmd"));
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
                return Err("Choose the absolute path to the Claude executable.".to_string());
            }
            Ok(path)
        }
        None => Ok(discover_binary().unwrap_or_else(|| PathBuf::from("claude.exe"))),
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
    "Claude Code was not found. Install it or choose the Claude executable in the assistant settings.".to_string()
}

#[tauri::command]
pub fn claude_locate() -> ClaudeLocation {
    ClaudeLocation {
        path: discover_binary().map(|path| path.to_string_lossy().into_owned()),
        searched: candidate_binaries()
            .iter()
            .map(|path| path.to_string_lossy().into_owned())
            .collect(),
    }
}

#[tauri::command]
pub fn claude_cancel(request_id: String, state: State<'_, ClaudeState>) -> Result<(), String> {
    let jobs = state
        .jobs
        .lock()
        .map_err(|_| "Claude state unavailable.".to_string())?;
    if let Some(cancel) = jobs.get(&request_id) {
        let _ = cancel.send(true);
    }
    Ok(())
}

#[tauri::command]
pub async fn claude_operation(
    app: AppHandle,
    request_id: String,
    operation: String,
    executable: Option<String>,
    body: Option<Value>,
    state: State<'_, ClaudeState>,
) -> Result<Value, String> {
    if !matches!(operation.as_str(), "status" | "login" | "logout" | "response") {
        return Err("Unsupported Claude operation.".to_string());
    }
    let (cancel, mut cancelled) = watch::channel(false);
    {
        let mut jobs = state
            .jobs
            .lock()
            .map_err(|_| "Claude state unavailable.".to_string())?;
        if !jobs.is_empty() {
            return Err("A Claude operation is already running.".to_string());
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
            run(&app, &operation, executable, body.unwrap_or(Value::Null)),
        ) => result.unwrap_or_else(|_| Err("The Claude operation timed out.".to_string())),
        _ = cancelled.changed() => Err("Stopped.".to_string()),
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
) -> Result<Value, String> {
    let binary = resolve_binary(executable)?;
    match operation {
        "status" => run_status(&binary).await,
        "login" => {
            run_simple(&binary, &["auth", "login"], LONG_TIMEOUT).await?;
            Ok(json!({ "connected": true }))
        }
        "logout" => {
            run_simple(&binary, &["auth", "logout"], SHORT_TIMEOUT).await?;
            Ok(json!({ "connected": false }))
        }
        _ => run_response(app, &binary, &body).await,
    }
}

async fn run_simple(binary: &Path, args: &[&str], timeout: Duration) -> Result<String, String> {
    let mut process = command(binary);
    process
        .args(args)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .kill_on_drop(true);
    let output = match tokio::time::timeout(timeout, process.output()).await {
        Ok(Ok(output)) => output,
        Ok(Err(error)) if error.kind() == std::io::ErrorKind::NotFound => return Err(not_found_message()),
        Ok(Err(_)) => return Err("Claude Code could not start.".to_string()),
        Err(_) => return Err("The Claude operation timed out.".to_string()),
    };
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if output.status.success() {
        return Ok(stdout);
    }
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
    let detail = if stderr.is_empty() { stdout } else { stderr };
    Err(if detail.is_empty() {
        "Claude Code could not complete the operation.".to_string()
    } else {
        truncate(&detail, 400)
    })
}

async fn run_status(binary: &Path) -> Result<Value, String> {
    let output = run_simple(binary, &["auth", "status"], SHORT_TIMEOUT).await;
    let Ok(text) = output else {
        return Ok(json!({ "connected": false, "account": null }));
    };
    let status: Value = serde_json::from_str(&text).map_err(|_| "Claude returned an invalid auth status.".to_string())?;
    let connected = status["loggedIn"].as_bool().unwrap_or(false)
        || status["authenticated"].as_bool().unwrap_or(false)
        || status["connected"].as_bool().unwrap_or(false);
    if !connected {
        return Ok(json!({ "connected": false, "account": null }));
    }
    Ok(json!({
        "connected": true,
        "account": {
            "type": "claude",
            "authenticated": true,
            "email": status["email"].as_str(),
            "planType": status["subscriptionType"].as_str().or_else(|| status["planType"].as_str())
        }
    }))
}

async fn run_response(app: &AppHandle, binary: &Path, body: &Value) -> Result<Value, String> {
    let workspace = app
        .path()
        .app_data_dir()
        .map_err(|_| "Application storage unavailable.".to_string())?
        .join("assistant-claude")
        .join("workspace");
    std::fs::create_dir_all(&workspace)
        .map_err(|error| format!("Could not prepare Claude storage: {error}"))?;
    let schema = output_schema();
    let message = build_message(body);
    let mut process = command(binary);
    process
        .args([
            "-p",
            "--input-format",
            "stream-json",
            "--output-format",
            "stream-json",
            "--verbose",
            "--safe-mode",
            "--disable-slash-commands",
            "--no-session-persistence",
            "--tools",
            "",
            "--json-schema",
            &schema.to_string(),
        ])
        .env_remove("ANTHROPIC_API_KEY")
        .env_remove("ANTHROPIC_AUTH_TOKEN")
        .current_dir(workspace)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .kill_on_drop(true);
    if let Some(model) = body["model"].as_str().filter(|model| !model.is_empty()) {
        process.arg("--model").arg(model);
    }
    let mut child = process.spawn().map_err(|error| match error.kind() {
        std::io::ErrorKind::NotFound => not_found_message(),
        std::io::ErrorKind::PermissionDenied => "Permission to run Claude Code was denied.".to_string(),
        _ => "Claude Code could not start.".to_string(),
    })?;
    let mut stdin = child.stdin.take().ok_or("Claude input unavailable.")?;
    stdin
        .write_all(format!("{message}\n").as_bytes())
        .await
        .map_err(|_| "The Claude connection closed.".to_string())?;
    drop(stdin);
    let output = child
        .wait_with_output()
        .await
        .map_err(|_| "The Claude connection failed.".to_string())?;
    if output.stdout.len() > MAX_OUTPUT_BYTES || output.stderr.len() > MAX_OUTPUT_BYTES {
        return Err("The Claude response exceeded the size limit.".to_string());
    }
    let stdout = String::from_utf8_lossy(&output.stdout);
    let result = stdout
        .lines()
        .filter_map(|line| serde_json::from_str::<Value>(line).ok())
        .find(|value| value["type"] == "result")
        .ok_or_else(|| {
            let detail = String::from_utf8_lossy(&output.stderr);
            if detail.trim().is_empty() {
                "Claude closed before returning a result.".to_string()
            } else {
                truncate(detail.trim(), 400)
            }
        })?;
    if result["subtype"] != "success" || result["is_error"] == true {
        let message = result["errors"]
            .as_array()
            .and_then(|errors| errors.first())
            .and_then(Value::as_str)
            .unwrap_or("Claude could not complete the response.");
        return Err(truncate(message, 400));
    }
    result["structured_output"]
        .as_object()
        .map(|value| Value::Object(value.clone()))
        .ok_or_else(|| "Claude did not return structured output.".to_string())
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

fn build_message(body: &Value) -> Value {
    let mut transcript = body["input"].clone();
    let mut images = Vec::new();
    if let Some(items) = transcript.as_array_mut() {
        for item in items {
            if let Some(content) = item["content"].as_array_mut() {
                for part in content.iter_mut() {
                    if part["type"] != "input_image" {
                        continue;
                    }
                    if let Some((media_type, data)) = parse_data_url(part["image_url"].as_str().unwrap_or_default()) {
                        images.push(json!({ "type": "image", "source": {
                            "type": "base64", "media_type": media_type, "data": data
                        }}));
                    }
                    *part = json!({ "type": "input_text", "text": "[Attached image]" });
                }
            }
        }
    }
    let text = format!(
        "{}\nDo not use local, network, or application tools. Available Geti application tools: {}\n\
         Continue this conversation: {}\nReturn only the requested structured result. Each call's arguments must be a JSON-encoded string.",
        body["instructions"].as_str().unwrap_or_default(),
        body["tools"],
        transcript
    );
    let mut content = vec![json!({ "type": "text", "text": text })];
    content.extend(images);
    json!({
        "type": "user",
        "message": { "role": "user", "content": content },
        "parent_tool_use_id": null
    })
}

fn parse_data_url(url: &str) -> Option<(&str, &str)> {
    let payload = url.strip_prefix("data:")?;
    let (metadata, data) = payload.split_once(',')?;
    let media_type = metadata.strip_suffix(";base64")?;
    if !matches!(media_type, "image/jpeg" | "image/png" | "image/gif" | "image/webp") || data.is_empty() {
        return None;
    }
    Some((media_type, data))
}

fn truncate(text: &str, limit: usize) -> String {
    match text.char_indices().nth(limit) {
        Some((cut, _)) => format!("{}...", &text[..cut]),
        None => text.to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::{build_message, parse_data_url};
    use serde_json::json;

    #[test]
    fn sends_images_as_sdk_content_blocks() {
        let body = json!({
            "instructions": "Annotate.",
            "tools": [],
            "input": [{ "type": "message", "role": "user", "content": [
                { "type": "input_image", "image_url": "data:image/png;base64,AA" }
            ]}]
        });
        let message = build_message(&body);
        assert_eq!(message["message"]["content"][1]["type"], "image");
        assert_eq!(parse_data_url("data:text/plain;base64,AA"), None);
    }
}