// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

use std::collections::HashMap;
use std::sync::Mutex;
use std::time::Duration;

use futures_util::StreamExt;
use serde::Serialize;
use serde_json::Value;
use tauri::ipc::Channel;
use tauri::State;
use tokio::sync::watch;

const KEYRING_SERVICE: &str = "com.intel.geti.assistant";
const OPENAI_ACCOUNT: &str = "openai-api-key";
const ANTHROPIC_ACCOUNT: &str = "anthropic-api-key";
const OPENAI_URL: &str = "https://api.openai.com/v1/responses";
const ANTHROPIC_URL: &str = "https://api.anthropic.com/v1/messages";
const CONNECT_TIMEOUT: Duration = Duration::from_secs(30);
const HEADERS_TIMEOUT: Duration = Duration::from_secs(60);
const IDLE_TIMEOUT: Duration = Duration::from_secs(180);
const MAX_STREAM_BYTES: usize = 32 * 1024 * 1024;
const MAX_CONCURRENT_REQUESTS: usize = 8;

#[derive(Default)]
pub struct ApiState {
    jobs: Mutex<HashMap<String, watch::Sender<bool>>>,
}

#[derive(Clone, Serialize)]
#[serde(tag = "type", rename_all = "camelCase")]
pub enum OpenAiEvent {
    Delta {
        text: String,
    },
    Completed {
        response: Value,
    },
    Failed {
        message: String,
        status: Option<u16>,
        code: Option<String>,
    },
}

#[derive(Clone, Serialize)]
#[serde(tag = "type", rename_all = "camelCase")]
pub enum AnthropicEvent {
    Sse { data: String },
    Failed { message: String },
    Cancelled,
}

fn checked_account(account: &str) -> Result<&str, String> {
    match account {
        OPENAI_ACCOUNT | ANTHROPIC_ACCOUNT => Ok(account),
        _ => Err("Unsupported assistant credential.".to_string()),
    }
}

fn entry(account: &str) -> Result<keyring::Entry, String> {
    keyring::Entry::new(KEYRING_SERVICE, checked_account(account)?)
        .map_err(|_| "The Windows credential store is unavailable.".to_string())
}

fn stored_key(account: &str) -> Result<Option<String>, String> {
    match entry(account)?.get_password() {
        Ok(key) => Ok(Some(key)),
        Err(keyring::Error::NoEntry) => Ok(None),
        Err(_) => Err("Could not read the API key from Windows Credential Manager.".to_string()),
    }
}

#[tauri::command]
pub fn assistant_key_set(account: String, key: String) -> Result<(), String> {
    let key = key.trim();
    if key.is_empty() {
        return Err("Enter an API key.".to_string());
    }

    entry(&account)?
        .set_password(key)
        .map_err(|_| "Could not store the API key in Windows Credential Manager.".to_string())
}

#[tauri::command]
pub fn assistant_key_delete(account: String) -> Result<(), String> {
    match entry(&account)?.delete_credential() {
        Ok(()) | Err(keyring::Error::NoEntry) => Ok(()),
        Err(_) => Err("Could not remove the API key from Windows Credential Manager.".to_string()),
    }
}

#[tauri::command]
pub fn assistant_key_status(account: String) -> Result<bool, String> {
    Ok(stored_key(&account)?.is_some())
}

fn begin_job(request_id: &str, state: &ApiState) -> Result<watch::Receiver<bool>, String> {
    let (cancel, cancelled) = watch::channel(false);
    let mut jobs = state
        .jobs
        .lock()
        .map_err(|_| "Assistant state unavailable.".to_string())?;

    if jobs.len() >= MAX_CONCURRENT_REQUESTS {
        return Err("Too many assistant requests are in flight.".to_string());
    }
    if jobs.contains_key(request_id) {
        return Err("That assistant request is already running.".to_string());
    }
    jobs.insert(request_id.to_string(), cancel);
    Ok(cancelled)
}

fn end_job(request_id: &str, state: &ApiState) {
    if let Ok(mut jobs) = state.jobs.lock() {
        jobs.remove(request_id);
    }
}

fn cancel_job(request_id: &str, state: &ApiState) -> Result<(), String> {
    let jobs = state
        .jobs
        .lock()
        .map_err(|_| "Assistant state unavailable.".to_string())?;
    if let Some(cancel) = jobs.get(request_id) {
        let _ = cancel.send(true);
    }
    Ok(())
}

#[tauri::command]
pub fn openai_cancel(request_id: String, state: State<'_, ApiState>) -> Result<(), String> {
    cancel_job(&request_id, &state)
}

#[tauri::command]
pub fn anthropic_cancel(request_id: String, state: State<'_, ApiState>) -> Result<(), String> {
    cancel_job(&request_id, &state)
}

#[tauri::command]
pub async fn openai_responses_stream(
    request_id: String,
    body: Value,
    on_event: Channel<OpenAiEvent>,
    state: State<'_, ApiState>,
) -> Result<(), String> {
    let key = stored_key(OPENAI_ACCOUNT)?
        .ok_or_else(|| "No OpenAI API key is stored. Add one in the assistant settings.".to_string())?;
    let mut cancelled = begin_job(&request_id, &state)?;

    let outcome = tokio::select! {
        result = run_openai(body, &key, &on_event) => result,
        _ = cancelled.changed() => fail_openai(&on_event, "Stopped.", None, None),
    };
    end_job(&request_id, &state);
    outcome
}

#[tauri::command]
pub async fn anthropic_messages_stream(
    request_id: String,
    body: Value,
    on_event: Channel<AnthropicEvent>,
    state: State<'_, ApiState>,
) -> Result<(), String> {
    let key = stored_key(ANTHROPIC_ACCOUNT)?
        .ok_or_else(|| "No Anthropic API key is stored. Add one in the assistant settings.".to_string())?;
    let mut cancelled = begin_job(&request_id, &state)?;

    let outcome = tokio::select! {
        result = run_anthropic(body, &key, &on_event) => result,
        _ = cancelled.changed() => {
            let _ = on_event.send(AnthropicEvent::Cancelled);
            Ok(())
        },
    };
    end_job(&request_id, &state);
    outcome
}

fn client() -> Result<reqwest::Client, String> {
    reqwest::Client::builder()
        .connect_timeout(CONNECT_TIMEOUT)
        .build()
        .map_err(|_| "Could not create an HTTPS client.".to_string())
}

async fn run_openai(
    mut body: Value,
    key: &str,
    on_event: &Channel<OpenAiEvent>,
) -> Result<(), String> {
    let Some(object) = body.as_object_mut() else {
        return Err("Invalid assistant request.".to_string());
    };
    object.insert("stream".to_string(), Value::Bool(true));
    object.insert("store".to_string(), Value::Bool(false));

    let request = client()?
        .post(OPENAI_URL)
        .bearer_auth(key)
        .header("accept", "text/event-stream")
        .json(&body)
        .send();
    let response = match tokio::time::timeout(HEADERS_TIMEOUT, request).await {
        Err(_) => return fail_openai(on_event, "OpenAI did not respond in time.", None, None),
        Ok(Err(error)) => {
            return fail_openai(
                on_event,
                &redact(&format!("Could not reach OpenAI: {error}"), key),
                None,
                None,
            )
        }
        Ok(Ok(response)) => response,
    };

    if !response.status().is_success() {
        let status = response.status().as_u16();
        let payload = response
            .text()
            .await
            .ok()
            .and_then(|text| serde_json::from_str::<Value>(&text).ok())
            .unwrap_or(Value::Null);
        let message = payload["error"]["message"]
            .as_str()
            .map(str::to_owned)
            .unwrap_or_else(|| format!("OpenAI returned HTTP {status}."));
        return fail_openai(
            on_event,
            &redact(&message, key),
            Some(status),
            payload["error"]["code"].as_str().map(str::to_owned),
        );
    }

    let mut stream = response.bytes_stream();
    let mut buffer = Vec::new();
    let mut received = 0usize;
    loop {
        let chunk = match tokio::time::timeout(IDLE_TIMEOUT, stream.next()).await {
            Err(_) => return fail_openai(on_event, "The OpenAI response stalled.", None, None),
            Ok(None) => break,
            Ok(Some(Err(error))) => {
                return fail_openai(
                    on_event,
                    &redact(&format!("The OpenAI stream failed: {error}"), key),
                    None,
                    None,
                )
            }
            Ok(Some(Ok(chunk))) => chunk,
        };
        received += chunk.len();
        if received > MAX_STREAM_BYTES {
            return fail_openai(on_event, "The OpenAI response exceeded the size limit.", None, None);
        }
        for line in drain_complete_lines(&mut buffer, &chunk) {
            if dispatch_openai(&line, on_event, key) {
                return Ok(());
            }
        }
    }
    fail_openai(
        on_event,
        "The OpenAI stream ended before the response completed.",
        None,
        None,
    )
}

async fn run_anthropic(
    mut body: Value,
    key: &str,
    on_event: &Channel<AnthropicEvent>,
) -> Result<(), String> {
    let Some(object) = body.as_object_mut() else {
        return Err("Invalid assistant request.".to_string());
    };
    object.insert("stream".to_string(), Value::Bool(true));

    let request = client()?
        .post(ANTHROPIC_URL)
        .header("x-api-key", key)
        .header("anthropic-version", "2023-06-01")
        .header("accept", "text/event-stream")
        .json(&body)
        .send();
    let response = match tokio::time::timeout(HEADERS_TIMEOUT, request).await {
        Err(_) => return fail_anthropic(on_event, "Anthropic did not respond in time."),
        Ok(Err(error)) => {
            return fail_anthropic(
                on_event,
                &redact(&format!("Could not reach Anthropic: {error}"), key),
            )
        }
        Ok(Ok(response)) => response,
    };

    if !response.status().is_success() {
        let status = response.status().as_u16();
        let payload = response
            .text()
            .await
            .ok()
            .and_then(|text| serde_json::from_str::<Value>(&text).ok())
            .unwrap_or(Value::Null);
        let message = payload["error"]["message"]
            .as_str()
            .map(str::to_owned)
            .unwrap_or_else(|| format!("Anthropic returned HTTP {status}."));
        return fail_anthropic(on_event, &redact(&message, key));
    }

    let mut stream = response.bytes_stream();
    let mut buffer = Vec::new();
    let mut received = 0usize;
    loop {
        let chunk = match tokio::time::timeout(IDLE_TIMEOUT, stream.next()).await {
            Err(_) => return fail_anthropic(on_event, "The Anthropic response stalled."),
            Ok(None) => break,
            Ok(Some(Err(error))) => {
                return fail_anthropic(
                    on_event,
                    &redact(&format!("The Anthropic stream failed: {error}"), key),
                )
            }
            Ok(Some(Ok(chunk))) => chunk,
        };
        received += chunk.len();
        if received > MAX_STREAM_BYTES {
            return fail_anthropic(on_event, "The Anthropic response exceeded the size limit.");
        }
        for line in drain_complete_lines(&mut buffer, &chunk) {
            if dispatch_anthropic(&line, on_event) {
                return Ok(());
            }
        }
    }
    fail_anthropic(
        on_event,
        "The Anthropic stream ended before the response completed.",
    )
}

fn fail_openai(
    on_event: &Channel<OpenAiEvent>,
    message: &str,
    status: Option<u16>,
    code: Option<String>,
) -> Result<(), String> {
    let _ = on_event.send(OpenAiEvent::Failed {
        message: message.to_string(),
        status,
        code,
    });
    Ok(())
}

fn fail_anthropic(on_event: &Channel<AnthropicEvent>, message: &str) -> Result<(), String> {
    let _ = on_event.send(AnthropicEvent::Failed {
        message: message.to_string(),
    });
    Ok(())
}

fn drain_complete_lines(buffer: &mut Vec<u8>, chunk: &[u8]) -> Vec<String> {
    buffer.extend_from_slice(chunk);
    let mut lines = Vec::new();
    while let Some(index) = buffer.iter().position(|byte| *byte == b'\n') {
        let line: Vec<u8> = buffer.drain(..=index).collect();
        lines.push(
            String::from_utf8_lossy(&line)
                .trim_end_matches(['\r', '\n'])
                .to_string(),
        );
    }
    lines
}

fn dispatch_openai(line: &str, on_event: &Channel<OpenAiEvent>, key: &str) -> bool {
    let Some(payload) = line.strip_prefix("data:").map(str::trim) else {
        return false;
    };
    if payload.is_empty() || payload == "[DONE]" {
        return payload == "[DONE]";
    }
    let Ok(event) = serde_json::from_str::<Value>(payload) else {
        return false;
    };

    match event["type"].as_str().unwrap_or_default() {
        "response.output_text.delta" => {
            if let Some(text) = event["delta"].as_str() {
                let _ = on_event.send(OpenAiEvent::Delta {
                    text: text.to_string(),
                });
            }
            false
        }
        "response.completed" => {
            let _ = on_event.send(OpenAiEvent::Completed {
                response: event["response"].clone(),
            });
            true
        }
        "response.failed" | "response.incomplete" | "error" => {
            let error = if event["error"].is_object() {
                &event["error"]
            } else {
                &event["response"]["error"]
            };
            let message = error["message"]
                .as_str()
                .unwrap_or("OpenAI could not complete the response.");
            let _ = on_event.send(OpenAiEvent::Failed {
                message: redact(message, key),
                status: None,
                code: error["code"].as_str().map(str::to_owned),
            });
            true
        }
        _ => false,
    }
}

fn dispatch_anthropic(line: &str, on_event: &Channel<AnthropicEvent>) -> bool {
    let Some(payload) = line.strip_prefix("data:").map(str::trim) else {
        return false;
    };
    if payload.is_empty() {
        return false;
    }
    let terminal = serde_json::from_str::<Value>(payload)
        .ok()
        .and_then(|event| event["type"].as_str().map(|kind| matches!(kind, "message_stop" | "error")))
        .unwrap_or(payload == "[DONE]");
    if payload != "[DONE]" {
        let _ = on_event.send(AnthropicEvent::Sse {
            data: payload.to_string(),
        });
    }
    terminal
}

fn redact(message: &str, key: &str) -> String {
    let message = if key.is_empty() {
        message.to_string()
    } else {
        message.replace(key, "[redacted]")
    };
    let mut output = String::with_capacity(message.len());
    let mut rest = message.as_str();
    while let Some(index) = rest.find("sk-") {
        output.push_str(&rest[..index]);
        output.push_str("[redacted]");
        rest = &rest[index..];
        let end = rest
            .find(|character: char| {
                !(character.is_ascii_alphanumeric() || character == '-' || character == '_')
            })
            .unwrap_or(rest.len());
        rest = &rest[end..];
    }
    output.push_str(rest);
    output
}

#[cfg(test)]
mod tests {
    use super::{checked_account, drain_complete_lines, redact};

    #[test]
    fn accepts_only_known_credential_accounts() {
        assert!(checked_account("openai-api-key").is_ok());
        assert!(checked_account("anthropic-api-key").is_ok());
        assert!(checked_account("other").is_err());
    }

    #[test]
    fn preserves_partial_lines_and_redacts_tokens() {
        let mut buffer = Vec::new();
        assert_eq!(drain_complete_lines(&mut buffer, b"data: one\r\ndata:"), ["data: one"]);
        assert_eq!(drain_complete_lines(&mut buffer, b" two\n"), ["data: two"]);
        assert_eq!(redact("bad sk-ant-secret key", ""), "bad [redacted] key");
    }
}