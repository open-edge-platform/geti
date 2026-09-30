// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { API_BASE_URL } from './client';
import { uploadDatasetArchiveResumable } from './upload-file';

const uploadUrl = 'http://localhost:3000/api/uploads/00000000-0000-0000-0000-000000000001';
let offset = 0;
let uploadedBytes: Uint8Array;
let rejectNextPatch = false;
let createdUploads = 0;

class FakeXmlHttpRequest {
    status = 0;
    responseText = '';
    withCredentials = false;
    onload: (() => void) | null = null;
    onerror: (() => void) | null = null;
    onabort: (() => void) | null = null;
    private method = '';
    private headers: Record<string, string> = {};
    private responseHeaders: Record<string, string> = {};

    open(method: string): void {
        this.method = method;
    }

    setRequestHeader(name: string, value: string): void {
        this.headers[name] = value;
    }

    getResponseHeader(name: string): string | null {
        return this.responseHeaders[name] ?? null;
    }

    abort(): void {
        this.onabort?.();
    }

    send(body: Blob | null): void {
        void (async () => {
            switch (this.method) {
                case 'POST':
                    if (this.headers['Tus-Resumable']) {
                        createdUploads += 1;
                        this.status = 201;
                        this.responseHeaders.Location = uploadUrl;
                    } else {
                        this.status = 201;
                        this.responseText = JSON.stringify({ id: 'staged-dataset-id' });
                    }
                    break;
                case 'HEAD':
                    this.status = 200;
                    this.responseHeaders['Upload-Offset'] = String(offset);
                    break;
                case 'PATCH':
                    if (rejectNextPatch) {
                        rejectNextPatch = false;
                        this.status = 409;
                        break;
                    }
                    if (Number(this.headers['Upload-Offset']) !== offset || body === null) {
                        this.status = 409;
                        break;
                    }
                    const bytes = new Uint8Array(
                        await new Promise<ArrayBuffer>((resolve, reject) => {
                            const reader = new FileReader();
                            reader.onload = () => resolve(reader.result as ArrayBuffer);
                            reader.onerror = () => reject(reader.error);
                            reader.readAsArrayBuffer(body);
                        })
                    );
                    uploadedBytes.set(bytes, offset);
                    offset += bytes.length;
                    this.status = 204;
                    this.responseHeaders['Upload-Offset'] = String(offset);
                    break;
            }
            this.onload?.();
        })();
    }
}

describe('resumable uploads', () => {
    beforeEach(() => {
        offset = 0;
        uploadedBytes = new Uint8Array(15);
        rejectNextPatch = false;
        createdUploads = 0;
        vi.stubGlobal('XMLHttpRequest', FakeXmlHttpRequest);
        window.localStorage.clear();
    });

    afterEach(() => vi.unstubAllGlobals());

    it('reports acknowledged bytes and returns the staged archive after transfer', async () => {
        const file = new File(['archive-content'], 'dataset.zip', { type: 'application/zip' });
        const progress: number[] = [];

        const stagedDataset = await uploadDatasetArchiveResumable(file, (bytesSent) => progress.push(bytesSent));

        expect(stagedDataset.id).toBeTruthy();
        expect(progress).toEqual([file.size]);
        expect(Array.from(uploadedBytes.slice(0, file.size))).toEqual(
            Array.from(new TextEncoder().encode('archive-content'))
        );
    });

    it('recovers from an offset conflict without duplicating bytes', async () => {
        rejectNextPatch = true;
        const file = new File(['archive-content'], 'retry.zip');

        await uploadDatasetArchiveResumable(file);

        expect(Array.from(uploadedBytes.slice(0, file.size))).toEqual(
            Array.from(new TextEncoder().encode('archive-content'))
        );
    });

    it('resumes an interrupted upload from the persisted server offset', async () => {
        const file = new File(['archive-content'], 'dataset.zip');
        const key = `geti:tus:dataset-archive::${file.name}:${file.size}:${file.lastModified}`;
        const apiOrigin = new URL(API_BASE_URL || window.location.origin, window.location.origin).origin;
        window.localStorage.setItem(key, new URL(new URL(uploadUrl).pathname, apiOrigin).toString());
        offset = 7;
        uploadedBytes.set(new TextEncoder().encode('archive').slice(0, offset));
        const progress: number[] = [];

        await uploadDatasetArchiveResumable(file, (bytesSent) => progress.push(bytesSent));

        expect(createdUploads).toBe(0);
        expect(progress).toEqual([7, file.size]);
        expect(Array.from(uploadedBytes.slice(0, file.size))).toEqual(
            Array.from(new TextEncoder().encode('archive-content'))
        );
        expect(window.localStorage.getItem(key)).toBeNull();
    });

    it('does not create an upload when cancelled before transfer', async () => {
        const controller = new AbortController();
        controller.abort();

        await expect(
            uploadDatasetArchiveResumable(new File(['data'], 'cancel.zip'), undefined, controller.signal)
        ).rejects.toHaveProperty('name', 'AbortError');
        expect(createdUploads).toBe(0);
    });
});
