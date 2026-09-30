// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { http, HttpResponse } from 'msw';

import { getMockedMediaImage } from './mock-media';
import { getMockedStagedDataset } from './mock-staged-dataset';

const uploads = new Map<string, { length: number; offset: number }>();
const protocolHeaders = { 'Tus-Resumable': '1.0.0' };

export const tusUploadHandlers = [
    http.options(
        '/api/uploads',
        () =>
            new HttpResponse(null, {
                status: 204,
                headers: {
                    ...protocolHeaders,
                    'Tus-Version': '1.0.0',
                    'Tus-Extension': 'creation,expiration,termination',
                    'Tus-Max-Size': String(10 * 1024 * 1024 * 1024),
                },
            })
    ),
    http.post('/api/uploads', ({ request }) => {
        const length = Number(request.headers.get('Upload-Length'));
        const uploadId = crypto.randomUUID();
        uploads.set(uploadId, { length, offset: 0 });

        return new HttpResponse(null, {
            status: 201,
            headers: {
                ...protocolHeaders,
                Location: new URL(`/api/uploads/${uploadId}`, request.url).toString(),
                'Upload-Length': String(length),
                'Upload-Offset': '0',
                'Upload-Expires': new Date(Date.now() + 60 * 60 * 1000).toUTCString(),
            },
        });
    }),
    http.head('/api/uploads/:uploadId', ({ params }) => {
        const upload = uploads.get(String(params.uploadId));
        if (!upload) {
            return new HttpResponse(null, { status: 404, headers: protocolHeaders });
        }

        return new HttpResponse(null, {
            status: 200,
            headers: {
                ...protocolHeaders,
                'Upload-Length': String(upload.length),
                'Upload-Offset': String(upload.offset),
            },
        });
    }),
    http.options(
        '/api/uploads/:uploadId',
        () => new HttpResponse(null, { status: 204, headers: { 'Tus-Version': '1.0.0' } })
    ),
    http.patch('/api/uploads/:uploadId', async ({ params, request }) => {
        const upload = uploads.get(String(params.uploadId));
        if (!upload) {
            return new HttpResponse(null, { status: 404, headers: protocolHeaders });
        }

        const offset = Number(request.headers.get('Upload-Offset'));
        if (offset !== upload.offset) {
            return new HttpResponse(null, { status: 409, headers: protocolHeaders });
        }
        upload.offset += (await request.arrayBuffer()).byteLength;
        return new HttpResponse(null, {
            status: 204,
            headers: { ...protocolHeaders, 'Upload-Offset': String(upload.offset) },
        });
    }),
    http.post('/api/projects/:projectId/dataset/media/tus', () =>
        HttpResponse.json(getMockedMediaImage({ id: crypto.randomUUID() }), { status: 201 })
    ),
    http.post('/api/staged_datasets/tus', () =>
        HttpResponse.json(getMockedStagedDataset({ id: crypto.randomUUID() }), { status: 201 })
    ),
];
