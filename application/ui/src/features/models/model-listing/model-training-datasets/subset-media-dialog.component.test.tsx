// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { DatasetRevisionItem } from '@/api/types';
import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';
import { getMockedLabel } from 'mocks/mock-labels';
import { getMockedPipeline } from 'mocks/mock-pipeline';
import { getMockedProject } from 'mocks/mock-project';
import { delay, HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { type SelectableModel } from '../../utils';
import { SubsetMediaDialog } from './subset-media-dialog.component';

const MEDIA_SIZE = 100;

vi.mock('../../../annotator/hooks/use-load-image-query.hook', async (importOriginal) => {
    const actual = await importOriginal<typeof import('../../../annotator/hooks/use-load-image-query.hook')>();

    return {
        ...actual,
        useLoadImageQuery: () => ({
            data: new ImageData(new Uint8ClampedArray(4 * MEDIA_SIZE * MEDIA_SIZE), MEDIA_SIZE, MEDIA_SIZE),
            isSuccess: true,
            isPlaceholderData: false,
        }),
    };
});

const label = getMockedLabel({ id: 'label-1' });

const item: DatasetRevisionItem = {
    id: 'media-1',
    format: 'jpg',
    width: MEDIA_SIZE,
    height: MEDIA_SIZE,
    subset: 'training',
};

const selectableModel: SelectableModel = {
    modelId: 'model-1',
    modelVariantId: 'variant-1',
    name: 'Model [FP16]',
};

const PREDICTION_DELAY_MS = 500;
const ANNOTATIONS_DELAY_MS = 500;

const annotationsResponse = {
    media_id: item.id,
    subset: item.subset,
    user_reviewed: true,
    prediction_model_id: null,
    annotations: [
        {
            shape: { type: 'rectangle' as const, x: 10, y: 10, width: 20, height: 20 },
            labels: [{ id: label.id }],
        },
    ],
};

const renderApp = ({ selectedModel }: { selectedModel?: SelectableModel } = { selectedModel: selectableModel }) => {
    return render(
        <SubsetMediaDialog
            item={item}
            onClose={vi.fn()}
            selectedModel={selectedModel}
            onSelectNextMediaItem={vi.fn()}
        />
    );
};

describe('SubsetMediaDialog', () => {
    let predictionRequests = 0;

    beforeEach(() => {
        predictionRequests = 0;

        server.use(
            http.get('/api/projects/{project_id}', () =>
                HttpResponse.json(
                    getMockedProject({ task: { task_type: 'detection', exclusive_labels: true, labels: [label] } })
                )
            ),
            http.get('/api/projects/{project_id}/pipeline', () => HttpResponse.json(getMockedPipeline())),
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', () =>
                HttpResponse.json(annotationsResponse)
            ),
            http.post('/api/projects/{project_id}/dataset/media/media:predict', async () => {
                predictionRequests += 1;

                await delay(PREDICTION_DELAY_MS);

                return HttpResponse.json({
                    predictions: [
                        {
                            media: { id: item.id },
                            prediction: [
                                {
                                    shape: { type: 'rectangle', x: 0, y: 0, width: 50, height: 50 },
                                    labels: [{ id: label.id }],
                                    confidences: [0.9],
                                },
                            ],
                        },
                    ],
                });
            })
        );
    });

    it('shows a loading overlay on the canvas while predictions are being fetched', async () => {
        renderApp();

        fireEvent.click(await screen.findByRole('button', { name: 'Prediction' }));

        const overlay = await screen.findByRole('progressbar', {}, { timeout: PREDICTION_DELAY_MS });

        await waitForElementToBeRemoved(overlay, { timeout: 2 * PREDICTION_DELAY_MS });
    });

    it('shows a loading overlay on the canvas while the annotations are being fetched', async () => {
        server.use(
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', async () => {
                await delay(ANNOTATIONS_DELAY_MS);

                return HttpResponse.json(annotationsResponse);
            })
        );

        renderApp();

        expect(await screen.findByRole('button', { name: 'Close' })).toBeInTheDocument();

        await waitForElementToBeRemoved(screen.getByRole('progressbar'), { timeout: 2 * ANNOTATIONS_DELAY_MS });
    });

    it('does not fetch predictions while the annotation mode is active', async () => {
        renderApp();

        expect(await screen.findByRole('button', { name: 'Annotation' })).toBeInTheDocument();
        expect(predictionRequests).toBe(0);
    });

    it('hides the loading overlay when switching back to the annotation mode while inference is still running', async () => {
        renderApp();

        fireEvent.click(await screen.findByRole('button', { name: 'Prediction' }));

        expect(await screen.findByRole('progressbar', {}, { timeout: PREDICTION_DELAY_MS })).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Annotation' }));

        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    it('hides the annotation/prediction toggle when the model cannot run inference', async () => {
        renderApp({ selectedModel: undefined });

        expect(await screen.findByRole('button', { name: 'Close' })).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'Prediction' })).not.toBeInTheDocument();
    });
});
