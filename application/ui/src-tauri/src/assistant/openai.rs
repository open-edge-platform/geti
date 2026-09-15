//! Desktop-only bridge to the OpenAI Responses API used by the Geti assistant.
//!
//! The webview never holds the API key: it is written to the operating system
//! credential store and only ever read inside this module, which performs the
//! HTTPS request itself and streams decoded SSE events back over a Tauri
//! channel. That keeps the secret out of the renderer's reach (and out of
//! devtools, crash dumps and `localStorage`), and lets a request be cancelled
//! from the UI without tearing down the whole webview fetch.

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
const KEYRING_USER: &str = "openai-api-key";
const RESPONSES_URL: &str = "https://api.openai.com/v1/responses";

const CONNECT_TIMEOUT: Duration = Duration::from_secs(30);
const HEADERS_TIMEOUT: Duration = Duration::from_secs(60);
/// A healthy stream emits token deltas continuously; a long silence means the
/// connection died in a way TCP has not noticed yet.
const IDLE_TIMEOUT: Duration = Duration::from_secs(180);
const MAX_STREAM_BYTES: usize = 32 * 1024 * 1024;
/// Upper bound on concurrent in-flight requests, so a runaway renderer cannot
/// open an unbounded number of sockets against the API.
const MAX_CONCURRENT_REQUESTS: usize = 8;

const CANCELLED: &str = "The assistant request was cancelled.";

#[derive(Default)]
pub struct OpenAiState {
    jobs: Mutex<HashMap<String, watch::Sender<bool>>>,
}

/// Events forwarded to the webview. Mirrors `StreamEvent` in
/// `src/features/ai-assistant/types.ts` — keep both sides in sync.
#[derive(Clone, Serialize)]
#[serde(tag = "type", rename_all = "camelCase")]
pub enum StreamEvent {
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

fn entry() -> Result<keyring::Entry, String> {
    keyring::Entry::new(KEYRING_SERVICE, KEYRING_USER)
        .map_err(|_| "The operating system credential store is unavailable.".to_string())
}

fn stored_key() -> Result<Option<String>, String> {
    match entry()?.get_password() {
        Ok(key) => Ok(Some(key)),
        Err(keyring::Error::NoEntry) => Ok(None),
        Err(_) => Err("Could not read the OpenAI API key from the credential store.".to_string()),
    }
}

#[tauri::command]
pub fn openai_key_set(key: String) -> Result<(), String> {
    let key = key.trim();
    if key.is_empty() {
        return Err("Enter an OpenAI API key.".to_string());
    }

    entry()?
        .set_password(key)
        .map_err(|_| "Could not store the OpenAI API key.".to_string())
}

#[tauri::command]
pub fn openai_key_delete() -> Result<(), String> {
    match entry()?.delete_credential() {
        Ok(()) | Err(keyring::Error::NoEntry) => Ok(()),
        Err(_) => Err("Could not remove the OpenAI API key.".to_string()),
    }
}

/// Reports *whether* a key is stored. The key itself is never returned.
#[tauri::command]
pub fn openai_key_status() -> Result<bool, String> {
    Ok(stored_key()?.is_some())
}

#[tauri::command]
pub fn openai_cancel(request_id: String, state: State<'_, OpenAiState>) {
    if let Ok(jobs) = state.jobs.lock() {
        if let Some(sender) = jobs.get(&request_id) {
            let _ = sender.send(true);
        }
    }
}

#[tauri::command]
pub async fn openai_responses_stream(
    request_id: String,
    body: Value,
    on_event: Channel<StreamEvent>,
    state: State<'_, OpenAiState>,
) -> Result<(), String> {
    let key = stored_key()?
        .ok_or_else(|| "No OpenAI API key is stored. Add one in the assistant settings.".to_string())?;

    let (cancel, mut cancelled) = watch::channel(false);
    {
        let mut jobs = state
            .jobs
            .lock()
            .map_err(|_| "Assistant state unavailable".to_string())?;

        if jobs.len() >= MAX_CONCURRENT_REQUESTS {
            return Err("Too many assistant requests are in flight.".to_string());
        }
        if jobs.contains_key(&request_id) {
            return Err("That assistant request is already running.".to_string());
        }
        jobs.insert(request_id.clone(), cancel);
    }

    let outcome = tokio::select! {
        result = run_stream(body, &key, &on_event) => result,
        _ = cancelled.changed() => Err(CANCELLED.to_string()),
    };

    if let Ok(mut jobs) = state.jobs.lock() {
        jobs.remove(&request_id);
    }

    outcome
}

async fn run_stream(mut body: Value, key: &str, on_event: &Channel<StreamEvent>) -> Result<(), String> {
    let Some(object) = body.as_object_mut() else {
        return Err("Invalid assistant request.".to_string());
    };
    object.insert("stream".to_string(), Value::Bool(true));

    let client = reqwest::Client::builder()
        .connect_timeout(CONNECT_TIMEOUT)
        .build()
        .map_err(|_| "Could not create an HTTPS client.".to_string())?;

    let request = client
        .post(RESPONSES_URL)
        .bearer_auth(key)
        .header("accept", "text/event-stream")
        .json(&body)
        .send();

    let response = tokio::time::timeout(HEADERS_TIMEOUT, request)
        .await
        .map_err(|_| "OpenAI did not respond in time.".to_string())?
        .map_err(|error| redact(&format!("Could not reach OpenAI: {error}"), key))?;

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

        let _ = on_event.send(StreamEvent::Failed {
            message: redact(&message, key),
            status: Some(status),
            code: payload["error"]["code"].as_str().map(str::to_owned),
        });
        return Ok(());
    }

    let mut stream = response.bytes_stream();
    let mut buffer: Vec<u8> = Vec::new();
    let mut received = 0usize;

    loop {
        let chunk = match tokio::time::timeout(IDLE_TIMEOUT, stream.next()).await {
            Err(_) => return fail(on_event, "The OpenAI response stalled."),
            Ok(None) => break,
            Ok(Some(Err(error))) => {
                let message = redact(&format!("The OpenAI stream failed: {error}"), key);
                return fail(on_event, &message);
            }
            Ok(Some(Ok(chunk))) => chunk,
        };

        received += chunk.len();
        if received > MAX_STREAM_BYTES {
            return fail(on_event, "The OpenAI response exceeded the size limit.");
        }

        for line in drain_complete_lines(&mut buffer, &chunk) {
            if dispatch(&line, on_event, key) {
                return Ok(());
            }
        }
    }

    fail(on_event, "The OpenAI stream ended before the response completed.")
}

fn fail(on_event: &Channel<StreamEvent>, message: &str) -> Result<(), String> {
    let _ = on_event.send(StreamEvent::Failed {
        message: message.to_string(),
        status: None,
        code: None,
    });
    Ok(())
}

/// Splits `chunk` into whole `\n`-terminated lines, keeping any trailing
/// partial line (and any partial UTF-8 sequence inside it) in `buffer` for the
/// next chunk.
fn drain_complete_lines(buffer: &mut Vec<u8>, chunk: &[u8]) -> Vec<String> {
    buffer.extend_from_slice(chunk);

    let mut lines = Vec::new();
    while let Some(index) = buffer.iter().position(|byte| *byte == b'\n') {
        let line: Vec<u8> = buffer.drain(..=index).collect();
        lines.push(String::from_utf8_lossy(&line).trim_end().to_string());
    }

    lines
}

/// Handles a single SSE line. Returns `true` when the stream reached a terminal
/// state and the caller should stop reading.
fn dispatch(line: &str, on_event: &Channel<StreamEvent>, key: &str) -> bool {
    let Some(payload) = line.strip_prefix("data:") else {
        return false;
    };
    let payload = payload.trim();

    if payload.is_empty() || payload == "[DONE]" {
        return payload == "[DONE]";
    }

    let Ok(event) = serde_json::from_str::<Value>(payload) else {
        return false;
    };

    match event["type"].as_str().unwrap_or_default() {
        "response.output_text.delta" => {
            if let Some(text) = event["delta"].as_str() {
                let _ = on_event.send(StreamEvent::Delta {
                    text: text.to_string(),
                });
            }
            false
        }
        "response.completed" => {
            let _ = on_event.send(StreamEvent::Completed {
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
                .map(str::to_owned)
                .unwrap_or_else(|| "OpenAI could not complete the response.".to_string());

            let _ = on_event.send(StreamEvent::Failed {
                message: redact(&message, key),
                status: None,
                code: error["code"].as_str().map(str::to_owned),
            });
            true
        }
        _ => false,
    }
}

/// Strips the stored key and any other `sk-…` token from text that is about to
/// be shown in the UI or written to the log.
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
            .find(|c: char| !(c.is_ascii_alphanumeric() || c == '-' || c == '_'))
            .unwrap_or(rest.len());
        rest = &rest[end..];
    }
    output.push_str(rest);

    output
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn splits_only_complete_lines() {
        let mut buffer = Vec::new();

        assert_eq!(drain_complete_lines(&mut buffer, b"data: a\ndata: "), vec!["data: a"]);
        assert_eq!(drain_complete_lines(&mut buffer, b"b\n"), vec!["data: b"]);
    }

    #[test]
    fn redacts_keys_and_tokens() {
        assert_eq!(redact("bad key sk-abc123 used", ""), "bad key [redacted] used");
        assert_eq!(redact("key XYZ used", "XYZ"), "key [redacted] used");
    }
}
