// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { HttpResponse, http as mswHttp } from 'msw';

import { http } from '../src/api/utils';

const settings = [{ channel: 0, color: '#FFFFFF', enabled: true, window_min: 0, window_max: 65535 }];

const png = Uint8Array.from(
    atob('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='),
    (character) => character.charCodeAt(0)
);

export const omeHandlers = [
    http.get('/api/projects/{project_id}/dataset/media/{media_id}/planes', ({ request, response }) => {
        const searchParams = new URL(request.url).searchParams;

        return response(200).json({
            items: [],
            pagination: {
                limit: Number(searchParams.get('limit') ?? 50),
                offset: Number(searchParams.get('offset') ?? 0),
                total: 0,
                count: 0,
            },
        });
    }),
    http.get('/api/projects/{project_id}/dataset/media/{media_id}/channel-view', ({ response }) =>
        response(200).json({ settings, is_default: true })
    ),
    http.put('/api/projects/{project_id}/dataset/media/{media_id}/channel-view', async ({ request, response }) =>
        response(200).json({ ...(await request.json()), is_default: false })
    ),
    mswHttp.get('*/api/projects/:projectId/dataset/media/:mediaId/render', ({ request }) => {
        const headers = {
            ETag: '"mock-ome-render"',
            'Access-Control-Expose-Headers': 'ETag',
            'Cache-Control': new URL(request.url).searchParams.has('c')
                ? 'private, max-age=31536000, immutable'
                : 'private, no-cache',
        };

        return request.headers.get('If-None-Match') === headers.ETag
            ? new HttpResponse(null, { status: 304, headers })
            : new HttpResponse(png, { headers: { ...headers, 'Content-Type': 'image/png' } });
    }),
];
