// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { getMockedDatasetRevision } from 'mocks/mock-dataset-revision';
import { getMockedQuantizeJob } from 'mocks/mock-job';
import { getMockedModel } from 'mocks/mock-model';
import { getMockedVariant } from 'mocks/mock-model-variant';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { $api } from '../../../../api';
import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { createQueryClient } from '../../../../query-client/query-client';
import { ModelVariantsTabs } from './model-variant-tabs.component';

const trainingRevision = getMockedDatasetRevision({ id: 'training-revision' });
const newerRevision = getMockedDatasetRevision({
    id: 'newer-revision',
    created_at: '2025-02-01T00:00:00.000000+00:00',
    item_counts: { training: 15, validation: 3, testing: 2, total: 20 },
});
const trainedModel = getMockedModel({
    training_info: { status: 'successful', dataset_revision_id: trainingRevision.id },
    variants: [getMockedVariant({ format: 'openvino', precision: 'fp16' })],
});

const openQuantizationDialog = async (queryClient = createQueryClient()) => {
    const user = userEvent.setup();
    render(<ModelVariantsTabs model={trainedModel} />, { queryClient });
    await user.click(screen.getByRole('button', { name: 'Start quantization' }));

    return { user, dialog: within(await screen.findByRole('dialog')) };
};

describe('ModelVariantsTabs', () => {
    it('shows a placeholder when the model has no variants', () => {
        render(<ModelVariantsTabs model={getMockedModel({ variants: [] })} />);

        expect(screen.getByText('No available model variants.')).toBeInTheDocument();
    });

    it('keeps rendering the variants and disables quantization once the weights are deleted', () => {
        const model = getMockedModel({
            files_deleted: true,
            variants: [getMockedVariant({ id: 'ov-1', format: 'openvino', precision: 'fp16', weights_size: 0 })],
        });

        render(<ModelVariantsTabs model={model} />);

        expect(screen.queryByText('No available model variants.')).not.toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Download model ov-1' })).toBeDisabled();
        expect(screen.getByRole('button', { name: 'Start quantization' })).toBeDisabled();
    });

    it('sizes calibration from the training subset of the model dataset revision', async () => {
        const submitJob = rs.fn();
        server.use(
            http.get('/api/projects/{project_id}/dataset_revisions', () =>
                HttpResponse.json([trainingRevision, newerRevision])
            ),
            http.post('/api/jobs', async ({ request }) => {
                submitJob(await request.json());
                return HttpResponse.json(getMockedQuantizeJob(), { status: 201 });
            })
        );

        const { user, dialog } = await openQuantizationDialog();
        const size = dialog.getByRole('textbox', { name: 'Change Max calibration size' });
        await waitFor(() => expect(size).toHaveValue(String(trainingRevision.item_counts.training)));

        await user.click(dialog.getByRole('checkbox', { name: 'Use full dataset' }));
        await user.click(dialog.getByRole('button', { name: 'Start quantization' }));

        await waitFor(() =>
            expect(submitJob).toHaveBeenCalledWith(
                expect.objectContaining({
                    job_type: 'quantize',
                    parameters: expect.objectContaining({
                        model_id: trainedModel.id,
                        max_calibration_subset_size: trainingRevision.item_counts.training,
                    }),
                })
            )
        );
    });

    it.each([
        { state: 'missing', revisions: [newerRevision] },
        { state: 'deleted', revisions: [{ ...trainingRevision, files_deleted: true }, newerRevision] },
    ])('disables quantization when the training dataset revision is $state', async ({ revisions }) => {
        const queryClient = createQueryClient();
        const { queryKey } = $api.queryOptions('get', '/api/projects/{project_id}/dataset_revisions', {
            params: { path: { project_id: '123' } },
        });
        server.use(http.get('/api/projects/{project_id}/dataset_revisions', () => HttpResponse.json(revisions)));

        const { dialog } = await openQuantizationDialog(queryClient);

        await waitFor(() => expect(queryClient.getQueryData(queryKey)).toEqual(revisions));
        expect(dialog.getByRole('button', { name: 'Start quantization' })).toBeDisabled();
    });
});
