// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { fireEvent, screen, waitFor } from '@testing-library/react';
import { getMockedDatasetStatistics } from 'mocks/mock-dataset-item';
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

        server.use(
            http.get('/api/projects/{project_id}', () => {
                return HttpResponse.json(getMockedProject({ id: '123' }));
            }),
            http.get('/api/projects/{project_id}/dataset/views', () => {
                return HttpResponse.json([{ id: 'view-1', project_id: '123', name: 'Canada signs' }]);
            }),
            http.get('/api/projects/{project_id}/dataset/items', () => {
                return HttpResponse.json({
                    pagination: { total: 10, offset: 0, limit: 0, count: 0 },
                    items: [],
                });
            }),
            http.post('/api/jobs', async ({ request }) => {
                exportRequestBody = (await request.json()) as Record<string, unknown>;

                return HttpResponse.json({ job_id: 'job-1' });
            })
        );

        render(
            <ImportDatasetDialogStateProvider>
                <ImportExport />
            </ImportDatasetDialogStateProvider>,
            { route: `/projects/123?${DATASET_VIEW_ID_PARAM}=view-1` }
        );

        fireEvent.click(await screen.findByRole('button', { name: /import export dataset/i }));
        fireEvent.click(await screen.findByRole('menuitem', { name: /Export dataset/i }));

        expect(await screen.findByRole('heading', { name: /Canada signs/i })).toBeVisible();

        fireEvent.click(screen.getByRole('button', { name: /export/i, hidden: false }));

        await waitFor(() => expect(exportRequestBody).toBeDefined());
        expect(exportRequestBody).toEqual(expect.objectContaining({ dataset_id: null, dataset_view_id: 'view-1' }));
    });
});
