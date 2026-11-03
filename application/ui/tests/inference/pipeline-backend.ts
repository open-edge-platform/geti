// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Pipeline, SinkConfig, SourceConfig } from '@/api/types';
import { getMockedPipeline } from 'mocks/mock-pipeline';
import { HttpResponse } from 'msw';

import { http } from '../fixtures';

interface PipelineBackendOptions {
    sources?: SourceConfig[];
    sinks?: SinkConfig[];
    pipeline?: Partial<Pipeline>;
}

/**
 * In-memory stand-in for the sources, sinks and pipeline endpoints, so that what the UI saves is what it
 * reads back on the next refetch — the list, the "In use" badge and the settings all reflect the requests.
 */
export const createPipelineBackend = ({ sources = [], sinks = [], pipeline = {} }: PipelineBackendOptions = {}) => {
    const state = {
        sources: [...sources],
        sinks: [...sinks],
        pipeline: getMockedPipeline({
            project_id: 'id-1',
            status: 'idle',
            source: null,
            sink: null,
            ...pipeline,
        }),
    };

    const handlers = [
        http.get('/api/projects/{project_id}/pipeline', () => HttpResponse.json(state.pipeline)),
        http.patch('/api/projects/{project_id}/pipeline', async ({ request }) => {
            const body = await request.json();

            if (body.source_id !== undefined) {
                state.pipeline.source = state.sources.find(({ id }) => id === body.source_id) ?? null;
            }

            if (body.sink_id !== undefined) {
                state.pipeline.sink = state.sinks.find(({ id }) => id === body.sink_id) ?? null;
            }

            return HttpResponse.json(state.pipeline);
        }),
        http.post('/api/projects/{project_id}/pipeline:disable', () => {
            state.pipeline.status = 'idle';

            return HttpResponse.json(null, { status: 204 });
        }),

        http.get('/api/sources', () => HttpResponse.json(state.sources)),
        http.post('/api/sources', async ({ request }) => {
            const source = (await request.json()) as SourceConfig;
            state.sources.push(source);

            return HttpResponse.json(source, { status: 201 });
        }),
        http.patch('/api/sources/{source_id}', async ({ params, request }) => {
            const changes = await request.json();
            const index = state.sources.findIndex(({ id }) => id === params.source_id);
            state.sources[index] = { ...state.sources[index], ...changes } as SourceConfig;

            return HttpResponse.json(state.sources[index]);
        }),
        http.delete('/api/sources/{source_id}', ({ params }) => {
            state.sources = state.sources.filter(({ id }) => id !== params.source_id);

            return HttpResponse.json(null, { status: 204 });
        }),
        http.post('/api/sources/{source_id}:test', () => {
            return HttpResponse.json({ reachable: true, latency_ms: 5, error: null });
        }),

        http.get('/api/sinks', () => HttpResponse.json(state.sinks)),
        http.post('/api/sinks', async ({ request }) => {
            const sink = { ...(await request.json()), id: crypto.randomUUID() } as SinkConfig;
            state.sinks.push(sink);

            return HttpResponse.json(sink, { status: 201 });
        }),
        http.patch('/api/sinks/{sink_id}', async ({ params, request }) => {
            const changes = await request.json();
            const index = state.sinks.findIndex(({ id }) => id === params.sink_id);
            state.sinks[index] = { ...state.sinks[index], ...changes } as SinkConfig;

            return HttpResponse.json(state.sinks[index]);
        }),
        http.delete('/api/sinks/{sink_id}', ({ params }) => {
            state.sinks = state.sinks.filter(({ id }) => id !== params.sink_id);

            return HttpResponse.json(null, { status: 204 });
        }),
        http.post('/api/sinks/{sink_id}:test', () => {
            return HttpResponse.json({ reachable: true, latency_ms: 5, error: null });
        }),
    ];

    return { state, handlers };
};
