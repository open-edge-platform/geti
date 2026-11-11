// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen, within } from '@testing-library/react';
import { getMockedDatasetRevision } from 'mocks/mock-dataset-revision';
import { getMockedTrainJob } from 'mocks/mock-job';
import { getMockedModel, getMockedModelArchitecture } from 'mocks/mock-model';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { RunningJobRow } from './running-job-row.component';

describe('RunningJobRow', () => {
    const mockModel = getMockedModel({
        id: 'model-123',
        architecture: 'arch-123',
        name: 'My Detection Model',
        training_info: {
            dataset_revision_id: 'dataset-123',
            status: 'in_progress',
            label_schema_revision: {
                labels: [
                    { id: '1', name: 'car' },
                    { id: '2', name: 'person' },
                ],
            },
        },
    });

    const modelArchitecture = getMockedModelArchitecture({
        performanceCategory: 'Speed',
        id: mockModel.architecture,
        name: 'Custom_Object_Detection_Gen3_ATSS',
    });

    beforeEach(() => {
        server.use(
            http.get('/api/projects/{project_id}/models/{model_id}', () => {
                return HttpResponse.json(mockModel);
            })
        );
    });

    it('renders all fields correctly, including both the architecture and the dataset', async () => {
        const job = getMockedTrainJob({
            metadata: {
                project: { id: '123' },
                model: {
                    id: mockModel.id,
                    name: mockModel.name,
                    architecture: modelArchitecture.id,
                    parent_revision_id: null,
                    dataset_revision_id: 'dataset-123',
                },
                device: {
                    type: 'cpu',
                    name: 'CPU',
                },
            },
            status: 'RUNNING',
            message: 'Running...',
            started_at: '2026-01-19T08:15:00.000000+00:00',
        });

        const datasetRevision = getMockedDatasetRevision({
            id: 'dataset-123',
            name: 'Dataset 1',
            item_counts: {
                total: 10,
                testing: 4,
                training: 4,
                validation: 2,
            },
        });

        render(
            <RunningJobRow job={job} datasetRevisions={[datasetRevision]} modelArchitectures={[modelArchitecture]} />
        );

        expect(await screen.findByText('My Detection Model')).toBeVisible();
        expect(screen.getByText('Running')).toBeVisible();
        expect(screen.getByText(/Started: Jan 19, 2026/i)).toBeVisible();
        expect(screen.getByText('Device: CPU')).toBeVisible();

        expect(screen.getByText(new RegExp(modelArchitecture.name))).toBeVisible();

        // The revision name only appears once the model behind the job has been fetched.
        expect(await screen.findByText(datasetRevision.name)).toBeVisible();
        const datasetBadge = screen.getByTestId('dataset-count');
        expect(within(datasetBadge).getByText(datasetRevision.item_counts?.total?.toString() ?? '')).toBeVisible();

        const labelsBadge = screen.getByTestId('labels-count');
        const labelSchemaRevision = mockModel.training_info.label_schema_revision ?? {};
        const labelsCount =
            'labels' in labelSchemaRevision && Array.isArray(labelSchemaRevision.labels)
                ? labelSchemaRevision.labels.length
                : '';
        expect(within(labelsBadge).getByText(labelsCount)).toBeVisible();
    });

    it('shows the dataset view a training job was started on, before its revision exists', async () => {
        const job = getMockedTrainJob({
            metadata: {
                project: { id: '123' },
                model: {
                    id: mockModel.id,
                    name: mockModel.name,
                    architecture: modelArchitecture.id,
                    parent_revision_id: null,
                    dataset_revision_id: null,
                    dataset_view_id: 'collection-one',
                    dataset_view_name: 'Collection One',
                },
                device: {
                    type: 'cpu',
                    name: 'CPU',
                },
            },
            status: 'RUNNING',
        });

        render(<RunningJobRow job={job} datasetRevisions={[]} modelArchitectures={[modelArchitecture]} />);

        expect(await screen.findByText('Collection One')).toBeVisible();
    });

    it('renders Cancel button when onCancel is provided and job is running', async () => {
        const mockCancel = rs.fn();
        const job = getMockedTrainJob({
            metadata: {
                project: { id: '123' },
                model: {
                    id: 'ef3983f1-cef0-4ebe-91db-7330f1dd6e27',
                    name: 'ATSS (ef3983f1)',
                    architecture: 'Custom_Object_Detection_Gen3_ATSS',
                    parent_revision_id: null,
                    dataset_revision_id: 'dataset-123',
                },
                device: {
                    type: 'cpu',
                    name: 'CPU',
                },
            },
            status: 'RUNNING',
        });

        render(
            <RunningJobRow
                job={job}
                onCancel={mockCancel}
                datasetRevisions={[]}
                modelArchitectures={[modelArchitecture]}
            />
        );

        const cancelButton = await screen.findByRole('button', { name: /cancel job/i });
        expect(cancelButton).toBeVisible();
        expect(cancelButton).toBeEnabled();
    });

    it('disables Cancel button when job is not running', async () => {
        const mockCancel = rs.fn();
        const job = getMockedTrainJob({
            metadata: {
                project: { id: '123' },
                model: {
                    id: 'ef3983f1-cef0-4ebe-91db-7330f1dd6e27',
                    name: 'ATSS (ef3983f1)',
                    architecture: 'Custom_Object_Detection_Gen3_ATSS',
                    parent_revision_id: null,
                    dataset_revision_id: 'dataset-123',
                },
                device: {
                    type: 'cpu',
                    name: 'CPU',
                },
            },
            status: 'FINISHED',
        });

        render(
            <RunningJobRow
                job={job}
                onCancel={mockCancel}
                datasetRevisions={[]}
                modelArchitectures={[modelArchitecture]}
            />
        );

        const cancelButton = await screen.findByRole('button', { name: /cancel job/i });
        expect(cancelButton).toBeDisabled();
    });
});
