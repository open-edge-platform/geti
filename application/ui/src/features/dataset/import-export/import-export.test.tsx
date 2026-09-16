// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { fireEvent, screen, waitFor } from '@testing-library/react';
import { getMockedDatasetStatistics } from 'mocks/mock-dataset-item';
import { getMockedJob } from 'mocks/mock-job';
import { getMockedProject } from 'mocks/mock-project';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../api/utils';
import { DATASET_VIEW_ID_PARAM } from '../../../hooks/use-dataset-view-id.hook';
import { server } from '../../../msw-node-setup';
import { ImportDatasetDialogStateProvider } from '../providers/export-import-dataset-dialog-provider.component';
import { ImportExport } from './import-export.component';

describe('ImportExport', () => {
    it('opens the export dialog when export option is selected', async () => {
        let datasetStatisticsRequests = 0;

        server.use(
            http.get('/api/projects/{project_id}', () => {
                return HttpResponse.json(getMockedProject({ id: '123' }));
            }),
            http.get('/api/projects/{project_id}/dataset/statistics', () => {
                datasetStatisticsRequests++;
                return HttpResponse.json(getMockedDatasetStatistics());
            }),
            http.get('/api/projects/{project_id}/dataset/items', () => {
                return HttpResponse.json({
                    pagination: {
                        total: 10,
                        offset: 0,
                        limit: 0,
                        count: 0,
                    },
                    items: [],
                });
            })
        );

        render(
            <ImportDatasetDialogStateProvider>
                <ImportExport />
            </ImportDatasetDialogStateProvider>
        );

        fireEvent.click(await screen.findByRole('button', { name: /import export dataset/i }));
        fireEvent.click(await screen.findByRole('menuitem', { name: /Export dataset/i }));

        expect(screen.getByRole('heading', { name: /Export settings/i })).toBeVisible();
        expect(datasetStatisticsRequests).toBe(0);

        fireEvent.click(screen.getByRole('radio', { name: 'COCO' }));
        await waitFor(() => expect(datasetStatisticsRequests).toBe(1));
    });

    it('exports the selected dataset view', async () => {
        let exportRequestBody: Record<string, unknown> | undefined;
        const datasetItemsViewIds: (string | null)[] = [];

        server.use(
            http.get('/api/projects/{project_id}', () => {
                return HttpResponse.json(getMockedProject({ id: '123' }));
            }),
            http.get('/api/projects/{project_id}/dataset/views', () => {
                return HttpResponse.json([
                    {
                        id: 'view-1',
                        project_id: '123',
                        name: 'Canada signs',
                        created_at: '2026-01-19T08:15:00.000000+00:00',
                    },
                ]);
            }),
            http.get('/api/projects/{project_id}/dataset/items', ({ request }) => {
                datasetItemsViewIds.push(new URL(request.url).searchParams.get('dataset_view_id'));

                return HttpResponse.json({
                    pagination: { total: 10, offset: 0, limit: 0, count: 0 },
                    items: [],
                });
            }),
            http.post('/api/jobs', async ({ request }) => {
                exportRequestBody = (await request.json()) as Record<string, unknown>;

                return HttpResponse.json(getMockedJob({ job_id: 'job-1' }));
            })
        );

        render(
            <ImportDatasetDialogStateProvider>
                <ImportExport />
            </ImportDatasetDialogStateProvider>,
            { route: `/projects/123?${DATASET_VIEW_ID_PARAM}=view-1` }
        );

        fireEvent.click(await screen.findByRole('button', { name: /import export dataset/i }));
        fireEvent.click(await screen.findByRole('menuitem', { name: 'Export dataset view' }));

        expect(await screen.findByRole('heading', { name: 'Export dataset view' })).toBeVisible();

        await waitFor(() => expect(datasetItemsViewIds.length).toBeGreaterThan(0));
        expect(datasetItemsViewIds.every((id) => id === 'view-1')).toBe(true);

        fireEvent.click(screen.getByRole('button', { name: 'Export' }));

        await waitFor(() => expect(exportRequestBody).toBeDefined());
        expect(exportRequestBody).toEqual(expect.objectContaining({ dataset_id: null, dataset_view_id: 'view-1' }));
    });
});
