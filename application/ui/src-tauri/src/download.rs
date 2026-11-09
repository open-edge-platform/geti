// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

//! Saves backend downloads to disk without passing them through the webview.

use std::fs::File;
use std::io::Write;
use std::path::{Path, PathBuf};

use reqwest::{Certificate, Client, ClientBuilder, Response, Url};
use serde::Deserialize;
use tauri::ipc::Channel;
use tauri::{AppHandle, Manager, WebviewWindow};
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
    let cert = backend_certificate(window.app_handle())?;
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

    let client = client_builder()
        .tls_certs_only([cert])
        .build()
        .map_err(|e| e.to_string())?;
    save(&client, url, &path)
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

/// The backend's self-signed certificate, which it serves from
/// `<data dir>/certs/localhost.pem` (see `application/backend/app/main.py`).
fn backend_certificate(app: &AppHandle) -> Result<Certificate, String> {
    let path = crate::resolve_data_dir(app)
        .ok_or("unknown data directory")?
        .join("certs")
        .join("localhost.pem");
    let pem = std::fs::read(&path).map_err(|e| format!("{}: {e}", path.display()))?;
    Certificate::from_pem(&pem).map_err(|e| e.to_string())
}

fn client_builder() -> ClientBuilder {
    Client::builder()
        // Loopback traffic must not go through a proxy set in HTTP(S)_PROXY.
        .no_proxy()
        // `backend_url` only checks the first URL, so never follow redirects.
        .redirect(reqwest::redirect::Policy::none())
}

/// Stream `url` into `<path>.part` and only replace `path` once it is complete,
/// so a failed download never destroys an existing file.
async fn save(client: &Client, url: Url, path: &Path) -> Result<(), String> {
    let mut response = client.get(url).send().await.map_err(|e| e.to_string())?;
    if !response.status().is_success() {
        return Err(format!("backend responded with {}", response.status()));
    }

    let part = part_path(path);
    let saved = write_body(&mut response, &part)
        .await
        .and_then(|()| std::fs::rename(&part, path).map_err(|e| e.to_string()));
    if saved.is_err() {
        let _ = std::fs::remove_file(&part);
    }
    saved
}

fn part_path(path: &Path) -> PathBuf {
    let mut name = path.file_name().unwrap_or_default().to_os_string();
    name.push(".part");
    path.with_file_name(name)
}

async fn write_body(response: &mut Response, path: &Path) -> Result<(), String> {
    let mut file = File::create(path).map_err(|e| e.to_string())?;
    while let Some(chunk) = response.chunk().await.map_err(|e| e.to_string())? {
        file.write_all(&chunk).map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use std::io::{Read, Write};
    use std::net::TcpListener;
    use std::path::{Path, PathBuf};

    use reqwest::Url;

    use super::{backend_url, client_builder, part_path, save};

    /// Serve one raw HTTP `response` on a random loopback port and return its URL.
    fn serve_once(response: &'static str) -> Url {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let url = Url::parse(&format!("http://{}/file", listener.local_addr().unwrap())).unwrap();
        std::thread::spawn(move || {
            let (mut stream, _) = listener.accept().unwrap();
            let mut request = Vec::new();
            let mut buf = [0; 1024];
            while !request.ends_with(b"\r\n\r\n") {
                let n = stream.read(&mut buf).unwrap();
                if n == 0 {
                    break;
                }
                request.extend_from_slice(&buf[..n]);
            }
            stream.write_all(response.as_bytes()).unwrap();
        });
        url
    }

    /// A fresh directory holding `file.zip` with `previous` contents, if any.
    fn target(test: &str, previous: Option<&str>) -> PathBuf {
        let dir = std::env::temp_dir().join(format!("geti-download-test-{test}"));
        let _ = std::fs::remove_dir_all(&dir);
        std::fs::create_dir_all(&dir).unwrap();
        let path = dir.join("file.zip");
        if let Some(previous) = previous {
            std::fs::write(&path, previous).unwrap();
        }
        path
    }

    fn download(response: &'static str, path: &Path) -> Result<(), String> {
        let client = client_builder().build().unwrap();
        tauri::async_runtime::block_on(save(&client, serve_once(response), path))
    }

    fn contents(path: &Path) -> Option<String> {
        std::fs::read_to_string(path).ok()
    }

    #[test]
    fn complete_download_replaces_the_file() {
        let path = target("complete", Some("old"));
        download("HTTP/1.1 200 OK\r\nContent-Length: 3\r\n\r\nnew", &path).unwrap();
        assert_eq!(contents(&path).as_deref(), Some("new"));
        assert!(!part_path(&path).exists());
    }

    #[test]
    fn interrupted_download_keeps_the_previous_file() {
        let path = target("interrupted", Some("old"));
        // The connection closes after 3 of the announced 10 bytes.
        assert!(download("HTTP/1.1 200 OK\r\nContent-Length: 10\r\n\r\nnew", &path).is_err());
        assert_eq!(contents(&path).as_deref(), Some("old"));
        assert!(!part_path(&path).exists());
    }

    #[test]
    fn interrupted_download_leaves_no_file() {
        let path = target("interrupted-new", None);
        assert!(download("HTTP/1.1 200 OK\r\nContent-Length: 10\r\n\r\nnew", &path).is_err());
        assert!(!path.exists());
        assert!(!part_path(&path).exists());
    }

    #[test]
    fn error_and_redirect_responses_are_not_saved() {
        for (test, response) in [
            (
                "error",
                "HTTP/1.1 500 Internal Server Error\r\nContent-Length: 3\r\n\r\nbad",
            ),
            (
                "redirect",
                "HTTP/1.1 302 Found\r\nLocation: http://example.com/\r\nContent-Length: 0\r\n\r\n",
            ),
        ] {
            let path = target(test, Some("old"));
            assert!(download(response, &path).is_err(), "{test} should fail");
            assert_eq!(
                contents(&path).as_deref(),
                Some("old"),
                "{test} changed the file"
            );
            assert!(!part_path(&path).exists());
        }
    }

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
