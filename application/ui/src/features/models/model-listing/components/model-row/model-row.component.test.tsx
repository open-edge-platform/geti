// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { getMockedDatasetRevision } from 'mocks/mock-dataset-revision';
import { render } from 'test-utils/render';

import { getMockedModel, getMockedModelArchitecture } from '../../../../../../mocks/mock-model';
import { formatDateTime, formatTrainingDateTime } from '../../../../../shared/date-utils';
import { formatBytes } from '../../../../../shared/util';
import { ModelRow } from './model-row.component';

describe('ModelRow', () => {
    const defaultModel = getMockedModel({
        id: 'model-123',
        name: 'Test Model',
        architecture: 'YOLOX',
        size: 1024,
        training_info: {
            status: 'successful',
            label_schema_revision: {
                labels: [
                    { id: 'label-1', name: 'cat' },
                    { id: 'label-2', name: 'dog' },
                ],
            },
            start_time: '2025-01-10T10:00:00.000000+00:00',
            end_time: '2025-01-10T12:30:00.000000+00:00',
            dataset_revision_id: 'dataset-123',
            device: {
                type: 'cuda',
                name: 'NVIDIA RTX 3090',
            },
        },
        variants: [
            {
                id: 'variant-123',
                format: 'pytorch',
                precision: 'fp32',
                weights_size: 1024,
                files_deleted: false,
                evaluations: [
                    {
                        dataset_revision_id: 'dataset-123',
                        subset: 'testing',
                        metrics: [{ name: 'mAP', value: 0.85, primary: true }],
                    },
                ],
            },
        ],
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

    const modelArchitecture = getMockedModelArchitecture({ performanceCategory: 'Speed' });

    describe('basic rendering', () => {
        it('renders all model information correctly when grouped by architecture', () => {
            render(
                <ModelRow
                    model={defaultModel}
                    datasetRevision={datasetRevision}
                    groupBy={'architecture'}
                    modelArchitecture={modelArchitecture}
                />
            );

            expect(screen.getByTestId('model-name')).toHaveTextContent('Test Model');
            expect(
                screen.getByText(formatTrainingDateTime(defaultModel.training_info.end_time).replace(/\n/g, ' '))
            ).toBeInTheDocument();

            const datasetBadge = screen.getByTestId('dataset-count');
            const labelsBadge = screen.getByTestId('labels-count');

            expect(screen.getByText(datasetRevision.name)).toBeInTheDocument();
            expect(screen.getByText(formatDateTime(datasetRevision.created_at))).toBeInTheDocument();
            expect(within(datasetBadge).getByText('10')).toBeInTheDocument();
            expect(within(labelsBadge).getByText('2')).toBeInTheDocument();

            expect(screen.getByTestId('device info')).toHaveTextContent('NVIDIA RTX 3090');
            expect(screen.getByTestId('model size')).toHaveTextContent(formatBytes(defaultModel.size));
            expect(screen.getByLabelText('Model accuracy')).toHaveTextContent('85%');

            expect(screen.queryByText(new RegExp(modelArchitecture.name))).not.toBeInTheDocument();
            expect(screen.queryByText(modelArchitecture.performanceCategory ?? '')).not.toBeInTheDocument();
        });

        it('renders all model information correctly when grouped by dataset', () => {
            render(
                <ModelRow
                    model={defaultModel}
                    datasetRevision={datasetRevision}
                    groupBy={'dataset'}
                    modelArchitecture={modelArchitecture}
                />
            );

            expect(screen.getByTestId('model-name')).toHaveTextContent('Test Model');
            expect(
                screen.getByText(formatTrainingDateTime(defaultModel.training_info.end_time).replace(/\n/g, ' '))
            ).toBeInTheDocument();

            expect(screen.getByText(`${modelArchitecture.name} (${modelArchitecture.license})`)).toBeInTheDocument();
            expect(screen.getByText(modelArchitecture.performanceCategory ?? '')).toBeInTheDocument();

            expect(screen.getByTestId('device info')).toHaveTextContent('NVIDIA RTX 3090');
            expect(screen.getByTestId('model size')).toHaveTextContent(formatBytes(defaultModel.size));
            expect(screen.getByLabelText('Model accuracy')).toHaveTextContent('85%');

            expect(screen.queryByText(datasetRevision.name)).not.toBeInTheDocument();
            expect(screen.queryByTestId('dataset-count')).not.toBeInTheDocument();
            expect(screen.queryByTestId('labels-count')).not.toBeInTheDocument();
        });

        it('renders "-" when model size is 0 or negative', () => {
            const modelWithZeroSize = getMockedModel({ size: 0 });

            render(
                <ModelRow
                    model={modelWithZeroSize}
                    datasetRevision={datasetRevision}
                    groupBy={'dataset'}
                    modelArchitecture={modelArchitecture}
                />
            );

            expect(screen.getByTestId('model size')).toHaveTextContent('-');
        });

        it('renders "Failed" badge when training status is failed', () => {
            const failedModel = getMockedModel({
                training_info: {
                    status: 'failed',
                },
            });

            render(
                <ModelRow
                    model={failedModel}
                    datasetRevision={datasetRevision}
                    groupBy={'dataset'}
                    modelArchitecture={modelArchitecture}
                />
            );

            expect(screen.getByText('Failed')).toBeInTheDocument();
        });

        it('renders "Deleted weights" badge when model files_deleted is true', () => {
            const deletedWeightsModel = getMockedModel({ files_deleted: true });

            render(
                <ModelRow
                    model={deletedWeightsModel}
                    datasetRevision={datasetRevision}
                    groupBy={'dataset'}
                    modelArchitecture={modelArchitecture}
                />
            );

            expect(screen.getByText('Deleted weights')).toBeInTheDocument();
        });

        it('does not render "Deleted weights" badge when model files_deleted is false', () => {
            render(
                <ModelRow
                    model={defaultModel}
                    datasetRevision={datasetRevision}
                    groupBy={'dataset'}
                    modelArchitecture={modelArchitecture}
                />
            );

            expect(screen.queryByText('Deleted weights')).not.toBeInTheDocument();
        });
    });

    describe('parent revision model', () => {
        it('renders parent revision model when provided and call onExpandModel when clicked', async () => {
            const onExpandModel = vi.fn();
            const parentModel = getMockedModel({
                id: 'parent-123',
                name: 'Parent Model',
            });

            render(
                <ModelRow
                    model={defaultModel}
                    parentRevisionModel={parentModel}
                    onExpandModel={onExpandModel}
                    datasetRevision={datasetRevision}
                    groupBy={'dataset'}
                    modelArchitecture={modelArchitecture}
                />
            );

            expect(screen.getByText('Fine-tuned from')).toBeInTheDocument();
            const parentLink = screen.getByRole('link', { name: 'Parent Model' });
            expect(parentLink).toBeInTheDocument();

            await userEvent.click(parentLink);
            expect(onExpandModel).toHaveBeenCalledWith('parent-123');
        });

        it('does not render parent revision model when not provided', () => {
            render(
                <ModelRow
                    model={defaultModel}
                    datasetRevision={datasetRevision}
                    groupBy={'dataset'}
                    modelArchitecture={modelArchitecture}
                />
            );

            expect(screen.queryByText('Fine-tuned from')).not.toBeInTheDocument();
        });
    });
});
