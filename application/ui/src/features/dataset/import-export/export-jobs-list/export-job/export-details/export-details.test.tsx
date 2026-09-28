// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { ExportDatasetMetadata } from '@/api/types';
import { screen } from '@testing-library/react';
import { getMockedLabel } from 'mocks/mock-labels';
import { getMockedProject } from 'mocks/mock-project';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../../../api/utils';
import { server } from '../../../../../../msw-node-setup';
import { ExportJobDetails } from './export-details.component';

describe('ExportJobDetails', () => {
    const renderApp = (metadata: ExportDatasetMetadata) => {
        server.use(
            http.get('/api/projects/{project_id}', () => {
                return HttpResponse.json(
                    getMockedProject({
                        id: 'project-123',
                        task: {
                            labels: [
                                getMockedLabel({ id: 'label-1', name: 'label 1' }),
                                getMockedLabel({ id: 'label-2', name: 'label 2' }),
                                getMockedLabel({ id: 'label-3', name: 'label 3' }),
                            ],
                            task_type: 'detection',
                            exclusive_labels: false,
                        },
                    })
                );
            })
        );

        render(<ExportJobDetails metadata={metadata} />);
    };

    it('displays all labels when no specific labels are filtered', async () => {
        const metadata: ExportDatasetMetadata = {
            dataset_id: 'dataset-123',
            project_id: 'project-123',
            export_format: 'COCO',
            filters: {
                include_unannotated: true,
            },
        };

        renderApp(metadata);

        expect(await screen.findByText(/Labels:\s*label 1, label 2, label 3/)).toBeVisible();
    });

    it('displays selected labels when specific labels are filtered', async () => {
        const metadata: ExportDatasetMetadata = {
            dataset_id: 'dataset-123',
            project_id: 'project-123',
            export_format: 'YOLO',
            filters: {
                labels: ['label 1', 'label 2'],
                include_unannotated: true,
            },
        };

        renderApp(metadata);

        expect(await screen.findByText(/Labels:\s*label 1, label 2$/)).toBeVisible();
        expect(screen.queryByText(/label 3/)).not.toBeInTheDocument();
    });

    it('filters out labels that are not in the project', async () => {
        const metadata: ExportDatasetMetadata = {
            dataset_id: 'dataset-123',
            project_id: 'project-123',
            export_format: 'COCO',
            filters: {
                labels: ['label 1', 'NonExistentLabel'],
                include_unannotated: true,
            },
        };

        renderApp(metadata);

        expect(await screen.findByText(/Labels:\s*label 1$/)).toBeVisible();
        expect(screen.queryByText(/NonExistentLabel/)).not.toBeInTheDocument();
    });

    it('displays "Only media with annotations" when include_unannotated is false', async () => {
        const metadata: ExportDatasetMetadata = {
            dataset_id: 'dataset-123',
            project_id: 'project-123',
            export_format: 'COCO',
            filters: { include_unannotated: false },
        };

        renderApp(metadata);

        expect(await screen.findByText(/Only media with annotations/)).toBeVisible();
    });

    it('does not display "Only media with annotations" when include_unannotated is true', async () => {
        const metadata: ExportDatasetMetadata = {
            dataset_id: 'dataset-123',
            project_id: 'project-123',
            export_format: 'COCO',
            filters: { include_unannotated: true },
        };

        renderApp(metadata);

        await screen.findByText('COCO');

        expect(await screen.findByText(/All media/)).toBeVisible();
    });

    it('names the dataset view being exported', async () => {
        server.use(
            http.get('/api/projects/{project_id}/dataset/views', () => {
                return HttpResponse.json([
                    {
                        id: 'view-1',
                        project_id: 'project-123',
                        name: 'Canada signs',
                        created_at: '2026-01-19T08:15:00.000000+00:00',
                    },
                ]);
            })
        );

        renderApp({
            dataset_id: 'staged-dataset-123',
            dataset_view_id: 'view-1',
            project_id: 'project-123',
            export_format: 'COCO',
            filters: { include_unannotated: true },
        });

        expect(await screen.findByText('Export dataset view')).toBeVisible();
        expect(await screen.findByText('View: Canada signs')).toBeVisible();
    });

    it('falls back to a neutral label when the exported view no longer exists', async () => {
        server.use(
            http.get('/api/projects/{project_id}/dataset/views', () => {
                return HttpResponse.json([]);
            })
        );

        renderApp({
            dataset_id: 'staged-dataset-123',
            dataset_view_id: 'deleted-view',
            project_id: 'project-123',
            export_format: 'COCO',
            filters: { include_unannotated: true },
        });

        expect(await screen.findByText('View: Deleted view')).toBeVisible();
    });

    it('does not show a view row when the entire dataset was exported', async () => {
        renderApp({
            dataset_id: 'dataset-123',
            project_id: 'project-123',
            export_format: 'COCO',
            filters: { include_unannotated: true },
        });

        expect(await screen.findByText('Export dataset')).toBeVisible();
        expect(screen.queryByText(/^View: /)).not.toBeInTheDocument();
    });
});
