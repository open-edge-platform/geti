// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { API_BASE_URL } from './client';

const TUS_VERSION = '1.0.0';
const TUS_CHUNK_SIZE = 5 * 1024 * 1024;
const MAX_RETRIES = 3;

interface XhrResult {
    status: number;
    responseText: string;
    getResponseHeader: (name: string) => string | null;
}

const request = (
    url: string,
    method: string,
    headers: Record<string, string>,
    body?: Blob,
    signal?: AbortSignal
): Promise<XhrResult> => {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        if (signal?.aborted) {
            reject(new DOMException('File transfer was cancelled.', 'AbortError'));
            return;
        }
        xhr.open(method, url);
        xhr.withCredentials = true;
        Object.entries(headers).forEach(([name, value]) => xhr.setRequestHeader(name, value));
        const cleanup = () => signal?.removeEventListener('abort', abortRequest);
        const abortRequest = () => xhr.abort();
        xhr.onload = () => {
            cleanup();
            resolve(xhr);
        };
        xhr.onerror = () => {
            cleanup();
            reject(new Error('Network error while transferring the file.'));
        };
        xhr.onabort = () => {
            cleanup();
            reject(new Error('File transfer was cancelled.'));
        };
        signal?.addEventListener('abort', abortRequest, { once: true });
        xhr.send(body ?? null);
    });
};

const encodeMetadata = (metadata: Record<string, string>): string => {
    return Object.entries(metadata)
        .map(([key, value]) => {
            const bytes = new TextEncoder().encode(value);
            const binary = Array.from(bytes, (byte) => String.fromCharCode(byte)).join('');
            return `${key} ${btoa(binary)}`;
        })
        .join(',');
};

const storageKey = (purpose: string, file: File, metadata: Record<string, string>): string =>
    `geti:tus:${purpose}:${metadata.project_id ?? ''}:${file.name}:${file.size}:${file.lastModified}`;

const readStoredUrl = (key: string): string | null => {
    try {
        const storedUrl = window.localStorage.getItem(key);
        if (!storedUrl) {
            return null;
        }
        const uploadUrl = new URL(storedUrl, window.location.origin);
        const apiOrigin = new URL(API_BASE_URL || window.location.origin, window.location.origin).origin;
        return uploadUrl.origin === apiOrigin && uploadUrl.pathname.startsWith('/api/uploads/')
            ? uploadUrl.toString()
            : null;
    } catch {
        return null;
    }
};

const storeUrl = (key: string, url: string | null): void => {
    try {
        if (url === null) {
            window.localStorage.removeItem(key);
        } else {
            window.localStorage.setItem(key, url);
        }
    } catch {
        // Resumability remains available for the current session when browser storage is unavailable.
    }
};

const uploadOffset = async (url: string, signal?: AbortSignal): Promise<number> => {
    const response = await request(url, 'HEAD', { 'Tus-Resumable': TUS_VERSION }, undefined, signal);
    if (response.status < 200 || response.status >= 300) {
        throw new Error(`Could not resume file transfer (HTTP ${response.status}).`);
    }

    const offset = response.getResponseHeader('Upload-Offset');
    if (offset === null || !/^\d+$/.test(offset)) {
        throw new Error('The upload server returned an invalid byte offset.');
    }

    return Number(offset);
};

const createUpload = async (
    file: File,
    purpose: string,
    metadata: Record<string, string>,
    signal?: AbortSignal
): Promise<string> => {
    const endpoint = `${API_BASE_URL.replace(/\/$/, '')}/api/uploads`;
    const response = await request(
        endpoint,
        'POST',
        {
            'Tus-Resumable': TUS_VERSION,
            'Upload-Length': String(file.size),
            'Upload-Metadata': encodeMetadata({ ...metadata, filename: file.name, purpose }),
        },
        undefined,
        signal
    );
    if (response.status !== 201) {
        throw new Error(`Could not start file transfer (HTTP ${response.status}).`);
    }

    const location = response.getResponseHeader('Location');
    if (!location) {
        throw new Error('The upload server did not return an upload location.');
    }

    const uploadPath = new URL(location, new URL(endpoint, window.location.origin)).pathname;
    if (!/^\/api\/uploads\/[0-9a-f-]{36}$/i.test(uploadPath)) {
        throw new Error('The upload server returned an invalid upload location.');
    }
    return new URL(uploadPath, new URL(endpoint, window.location.origin)).toString();
};

const transferChunks = async (
    file: File,
    uploadUrl: string,
    onProgress?: (bytesSent: number) => void,
    signal?: AbortSignal
): Promise<void> => {
    let offset = await uploadOffset(uploadUrl, signal);
    if (offset > 0) {
        onProgress?.(offset);
    }
    while (offset < file.size) {
        if (signal?.aborted) {
            throw new DOMException('File transfer was cancelled.', 'AbortError');
        }
        let patched = false;

        for (let attempt = 0; attempt < MAX_RETRIES && !patched; attempt += 1) {
            const chunk = file.slice(offset, Math.min(offset + TUS_CHUNK_SIZE, file.size));
            let response: XhrResult;
            try {
                response = await request(
                    uploadUrl,
                    'PATCH',
                    {
                        'Tus-Resumable': TUS_VERSION,
                        'Upload-Offset': String(offset),
                        'Content-Type': 'application/offset+octet-stream',
                    },
                    chunk,
                    signal
                );
            } catch (error) {
                if (signal?.aborted) {
                    throw error;
                }
                if (attempt === MAX_RETRIES - 1) {
                    throw error;
                }
                offset = await uploadOffset(uploadUrl, signal);
                if (offset >= file.size) {
                    patched = true;
                    onProgress?.(offset);
                }
                continue;
            }

            if (response.status !== 204) {
                if (response.status === 409) {
                    const serverOffset = await uploadOffset(uploadUrl, signal);
                    offset = serverOffset;
                    if (offset >= file.size) {
                        patched = true;
                        onProgress?.(offset);
                    }
                    continue;
                }
                throw new Error(`File transfer failed (HTTP ${response.status}).`);
            }
            const nextOffset = response.getResponseHeader('Upload-Offset');
            if (nextOffset === null || Number(nextOffset) !== offset + chunk.size) {
                throw new Error('The upload server acknowledged an unexpected byte offset.');
            }
            offset = Number(nextOffset);
            patched = true;
            onProgress?.(offset);
        }
        if (!patched) {
            throw new Error('The upload server repeatedly rejected the current byte offset.');
        }
    }
};

/** Transfer a file through TUS, then invoke the endpoint that consumes the completed upload. */
export const uploadWithTus = async <T>(
    purpose: string,
    file: File,
    consumeUrl: string,
    onProgress?: (bytesSent: number) => void,
    signal?: AbortSignal,
    metadata: Record<string, string> = {}
): Promise<T> => {
    const key = storageKey(purpose, file, metadata);
    let uploadUrl = readStoredUrl(key);
    if (uploadUrl) {
        try {
            await uploadOffset(uploadUrl, signal);
        } catch {
            if (signal?.aborted) {
                throw new DOMException('File transfer was cancelled.', 'AbortError');
            }
            storeUrl(key, null);
            uploadUrl = null;
        }
    }

    if (!uploadUrl) {
        uploadUrl = await createUpload(file, purpose, metadata, signal);
        storeUrl(key, uploadUrl);
    }

    await transferChunks(file, uploadUrl, onProgress, signal);
    const separator = consumeUrl.includes('?') ? '&' : '?';
    const uploadId = uploadUrl.split('/').at(-1) ?? '';
    const response = await request(
        `${API_BASE_URL.replace(/\/$/, '')}${consumeUrl}${separator}upload_id=${encodeURIComponent(uploadId)}`,
        'POST',
        { Accept: 'application/json' },
        undefined,
        signal
    );
    if (response.status < 200 || response.status >= 300) {
        throw new Error(`The file transferred, but the server could not process it (HTTP ${response.status}).`);
    }

    storeUrl(key, null);
    return JSON.parse(response.responseText) as T;
};
