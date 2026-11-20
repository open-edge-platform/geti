// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { getMockedPipeline } from 'mocks/mock-pipeline';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../api/utils';
import { server } from '../../../msw-node-setup';
import { DataCollection } from './data-collection.component';

describe('DataCollection', () => {
    const renderApp = (savePredictions = false, maxDatasetSize: number | null = 500) => {
        const pipelinePatchSpy = rs.fn();
        let pipeline = getMockedPipeline({
            data_collection: {
                max_dataset_size: maxDatasetSize,
                save_predictions: savePredictions,
                policies: [
                    { type: 'fixed_rate', rate: 12, enabled: true },
                    {
                        type: 'confidence_threshold',
                        confidence_threshold: 0.5,
                        min_sampling_interval: 2.5,
                        enabled: false,
                    },
                ],
            },
        });

        server.use(
            http.get('/api/projects/{project_id}/pipeline', () => HttpResponse.json(pipeline)),
            http.patch('/api/projects/{project_id}/pipeline', async ({ request }) => {
                const update = (await request.json()) as Partial<typeof pipeline>;
                pipelinePatchSpy(update);
                pipeline = { ...pipeline, data_collection: update.data_collection ?? pipeline.data_collection };

                return HttpResponse.json(pipeline);
            })
        );

        render(<DataCollection />);

        return pipelinePatchSpy;
    };

    beforeEach(() => {
        rs.resetAllMocks();
    });

    it('does not save predictions by default and toggles without changing collection policies', async () => {
        const user = userEvent.setup();
        const pipelinePatchSpy = renderApp();
        const toggle = await screen.findByRole('switch', { name: 'Save predictions as annotations' });

        expect(toggle).not.toBeChecked();
        await user.click(toggle);
        await waitFor(() => expect(toggle).toBeChecked());
        expect(pipelinePatchSpy).toHaveBeenLastCalledWith({
            data_collection: {
                max_dataset_size: 500,
                save_predictions: true,
                policies: [
                    { type: 'fixed_rate', rate: 12, enabled: true },
                    {
                        type: 'confidence_threshold',
                        confidence_threshold: 0.5,
                        min_sampling_interval: 2.5,
                        enabled: false,
                    },
                ],
            },
        });

        await user.click(toggle);
        await waitFor(() => expect(toggle).not.toBeChecked());
        expect(pipelinePatchSpy).toHaveBeenLastCalledWith({
            data_collection: expect.objectContaining({ save_predictions: false }),
        });
    });

    it('persists the displayed dataset size limit when the server has none', async () => {
        const user = userEvent.setup();
        const pipelinePatchSpy = renderApp(false, null);

        expect(await screen.findByLabelText('Size')).toHaveValue('500');
        await user.click(screen.getByRole('switch', { name: 'Save predictions as annotations' }));

        await waitFor(() =>
            expect(pipelinePatchSpy).toHaveBeenCalledWith({
                data_collection: expect.objectContaining({ save_predictions: true, max_dataset_size: 500 }),
            })
        );
    });

    it('keeps the previous setting when updating the pipeline fails', async () => {
        const user = userEvent.setup();
        renderApp();
        const request = rs.fn();
        server.use(
            http.patch('/api/projects/{project_id}/pipeline', () => {
                request();
                return new HttpResponse(null, { status: 500 });
            })
        );
        const toggle = await screen.findByRole('switch', { name: 'Save predictions as annotations' });

        await user.click(toggle);

        await waitFor(() => expect(request).toHaveBeenCalledOnce());
        await waitFor(() => expect(toggle).not.toBeDisabled());
        expect(toggle).not.toBeChecked();
    });

    it('renders Frames and Seconds fields for capture rate', async () => {
        renderApp();

        expect(await screen.findByLabelText('Frames')).toBeVisible();
        expect(screen.getByLabelText('Seconds')).toBeVisible();
        expect(screen.queryByLabelText('Rate')).not.toBeInTheDocument();
    });

    it.each([false, true])('preserves save_predictions=%s when changing capture rate', async (savePredictions) => {
        const pipelinePatchSpy = renderApp(savePredictions);

        const framesInput = await screen.findByLabelText('Frames');
        const secondsInput = screen.getByLabelText('Seconds');

        await userEvent.clear(framesInput);
        await userEvent.type(framesInput, '6');
        framesInput.blur();

        await waitFor(() => {
            expect(pipelinePatchSpy).toHaveBeenCalledWith(
                expect.objectContaining({
                    data_collection: expect.objectContaining({
                        save_predictions: savePredictions,
                        policies: expect.arrayContaining([
                            expect.objectContaining({
                                type: 'fixed_rate',
                                rate: 6, // 6 frames / 1 second
                            }),
                        ]),
                    }),
                })
            );
        });

        await userEvent.clear(secondsInput);
        await userEvent.type(secondsInput, '3');
        secondsInput.blur();

        await waitFor(() => {
            expect(pipelinePatchSpy).toHaveBeenLastCalledWith(
                expect.objectContaining({
                    data_collection: expect.objectContaining({
                        save_predictions: savePredictions,
                        policies: expect.arrayContaining([
                            expect.objectContaining({
                                type: 'fixed_rate',
                                rate: 2, // 6 frames / 3 seconds
                            }),
                        ]),
                    }),
                })
            );
        });

        expect(pipelinePatchSpy).toHaveBeenCalledTimes(2);
    });
});
