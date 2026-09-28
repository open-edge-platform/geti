// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

import { getMockedLabel } from 'mocks/mock-labels';
import { getMockedProject } from 'mocks/mock-project';
import { HttpResponse } from 'msw';

import { http, test } from '../fixtures';

const filename = fileURLToPath(import.meta.url);
const dirname = path.dirname(filename);

export const candyPngBuffer = fs.readFileSync(path.resolve(dirname, '../assets/candy.png'));

export const redLabel = getMockedLabel({ id: 'red-label', name: 'red-label', color: '#ad2323' });
export const blueLabel = getMockedLabel({ id: 'blue-label', name: 'blue-label', color: '#2424a0' });

export const candyBinaryHandler = http.get('/api/projects/{project_id}/dataset/media/{media_id}/binary', async () => {
    return HttpResponse.arrayBuffer(candyPngBuffer.buffer, {
        headers: { 'Content-Type': 'image/png' },
    });
});

export const mockedDetectionProject = getMockedProject({
    id: '123e4567-e89b-12d3-a456-426614174000',
    task: {
        exclusive_labels: true,
        task_type: 'detection',
        labels: [redLabel, blueLabel],
    },
});

// Shared network setup for the `mockedDetectionProject` used across the annotator.*.spec.ts files.
export const useDetectionProjectFixtures = () => {
    test.beforeEach(async ({ network }) => {
        network.use(
            http.get('/api/projects/{project_id}', () => {
                return HttpResponse.json(mockedDetectionProject);
            }),
            http.get('/api/projects', () => {
                return HttpResponse.json([mockedDetectionProject]);
            }),
            candyBinaryHandler,
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', async () => {
                return HttpResponse.json({
                    annotations: [],
                    user_reviewed: true,
                    subset: 'training',
                });
            })
        );
    });
};
