// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

//! Saves backend downloads to disk without passing them through the webview.

use std::fs::File;
use std::io::Write;
use std::path::Path;

use reqwest::{Response, Url};
use serde::Deserialize;
use tauri::ipc::Channel;
use tauri::WebviewWindow;
use tauri_plugin_dialog::DialogExt;

/// Where the backend side-car serves its API (see `PUBLIC_API_BASE_URL` in
/// `../rsbuild.config.ts`).
const BACKEND_ORIGIN: &str = "https://localhost:7860";

/// File type filter for the "Save as" dialog.
#[derive(Deserialize)]
pub struct SaveFilter {
    name: String,
    extensions: Vec<String>,
}

/// Ask the user where to save `url`, then stream the response into that file.
/// `on_started` fires once a destination is picked; cancelling is not an error.
#[tauri::command]
pub async fn download_file(
    window: WebviewWindow,
    url: String,
    file_name: String,
    filter: SaveFilter,
    on_started: Channel<()>,
) -> Result<(), String> {
    let url = backend_url(&url)?;
    let extensions: Vec<&str> = filter.extensions.iter().map(String::as_str).collect();
    // Blocking is fine here: async commands do not run on the main thread.
    let Some(path) = window
        .dialog()
        .file()
        .set_parent(&window)
        .set_file_name(file_name)
        .add_filter(filter.name, &extensions)
        .blocking_save_file()
    else {
        return Ok(());
    };
    let path = path.into_path().map_err(|e| e.to_string())?;
    let _ = on_started.send(());

    save(url, &path)
        .await
        .inspect_err(|e| log::error!("Download to {} failed: {e}", path.display()))
}

/// Only allow the backend, so the webview cannot use this to fetch other URLs.
fn backend_url(url: &str) -> Result<Url, String> {
    let url = Url::parse(url).map_err(|e| e.to_string())?;
    if url.origin().ascii_serialization() != BACKEND_ORIGIN {
        return Err(format!("not a backend URL: {url}"));
    }
    Ok(url)
}

async fn save(url: Url, path: &Path) -> Result<(), String> {
    let mut response = reqwest::Client::builder()
        // Loopback traffic must not go through a proxy set in HTTP(S)_PROXY.
        .no_proxy()
        // The backend's certificate is self-signed (the webview skips validation
        // too, see `tauri.conf.json`); `backend_url` limits this to the backend.
        .danger_accept_invalid_certs(true)
        .build()
        .map_err(|e| e.to_string())?
        .get(url)
        .send()
        .await
        .and_then(Response::error_for_status)
        .map_err(|e| e.to_string())?;

    // Only create (or truncate) the file once the backend has accepted the request.
    let mut file = File::create(path).map_err(|e| e.to_string())?;
    let written: Result<(), String> = async {
        while let Some(chunk) = response.chunk().await.map_err(|e| e.to_string())? {
            file.write_all(&chunk).map_err(|e| e.to_string())?;
        }
        Ok(())
    }
    .await;
    if written.is_err() {
        drop(file);
        let _ = std::fs::remove_file(path);
    }
    written
}

#[cfg(test)]
mod tests {
    use super::backend_url;

    #[test]
    fn only_backend_urls_are_allowed() {
        assert!(backend_url("https://localhost:7860/api/system/logs").is_ok());
        for url in [
            "http://localhost:7860/api/system/logs",
            "https://localhost:7861/api/system/logs",
            "https://example.com/api/system/logs",
            "file:///C:/Windows/win.ini",
            "/api/system/logs",
        ] {
            assert!(backend_url(url).is_err(), "{url} should be rejected");
        }
    }
}
