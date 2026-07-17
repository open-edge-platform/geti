// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { startTransition } from 'react';

import type { ImagesFolderSourceConfig, VideoFileSourceConfig } from '@/api/types';
import { act, screen, waitFor } from '@testing-library/react';
import { HttpResponse } from 'msw';
import { renderHook } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { prepareVideoFileFormData, videoFileBodyFormatter } from '../video-file/utils';
import { useSourceAction } from './use-source-action.hook';

const mockedConfig: ImagesFolderSourceConfig = {
    id: 'images_folder-id',
    name: 'Test Folder',
    source_type: 'images_folder',
    images_folder_path: '/path/to/images',
    ignore_existing_images: false,
};

const bodyFormatter = (formData: FormData) => ({
    id: String(formData.get('id')),
    name: String(formData.get('name')),
    source_type: 'images_folder' as const,
    images_folder_path: String(formData.get('images_folder_path')),
    ignore_existing_images: formData.get('ignore_existing_images') === 'on' ? true : false,
});

const renderApp = async ({
    isNewSource = false,
    config = mockedConfig,
    newResource = () => HttpResponse.error(),
    updateResource = () => HttpResponse.error(),
}) => {
    server.use(
        http.post('/api/sources', newResource),
        http.patch('/api/sources/{source_id}', updateResource),
        http.patch('/api/projects/{project_id}/pipeline', () =>
            HttpResponse.json({
                project_id: '',
                status: 'idle',
                device: 'images_folder',
            })
        )
    );

    const { result } = renderHook(() => useSourceAction({ config: mockedConfig, isNewSource, bodyFormatter }));
    const [_state, submitAction] = result.current;

    const formData = new FormData();
    formData.append('name', config.name);
    formData.append('source_type', config.source_type);
    formData.append('images_folder_path', config.images_folder_path);
    formData.append('ignore_existing_images', String(config.ignore_existing_images));
    config.id && formData.append('id', config.id);

    await act(async () => {
        startTransition(async () => submitAction(formData));
    });

    return result.current;
};

describe('useSourceAction', () => {
    it('return initial config', () => {
        const { result } = renderHook(() =>
            useSourceAction({ config: mockedConfig, isNewSource: true, bodyFormatter })
        );

        expect(result.current[0]).toEqual(mockedConfig);
    });

    describe('new configuration', () => {
        it('submits folder config and display error message on failure', async () => {
            const mockedError = 'test-error';
            await renderApp({
                isNewSource: true,
                newResource: () => HttpResponse.json({ detail: mockedError }, { status: 400 }),
            });

            await waitFor(() => {
                expect(screen.getByText(`Failed to save source configuration, ${mockedError}`)).toBeVisible();
            });
        });

        it('submit new image folder config and show success message', async () => {
            const mockedNewItemId = 'new-id-test';
            const [state] = await renderApp({
                isNewSource: true,
                newResource: () => HttpResponse.json({ ...mockedConfig, id: mockedNewItemId }),
            });

            await waitFor(() => {
                expect(screen.getByText('Source configuration created successfully.')).toBeVisible();
                expect(state.id).toBe(mockedNewItemId);
            });
        });
    });

    describe('edit configuration', () => {
        it('submits folder config and display error message on failure', async () => {
            const mockedError = 'test-error';

            await renderApp({
                isNewSource: false,
                updateResource: () => HttpResponse.json({ detail: mockedError }, { status: 400 }),
            });

            await waitFor(() => {
                expect(screen.getByText(`Failed to save source configuration, ${mockedError}`)).toBeVisible();
            });
        });

        it('submits folder config and show success message', async () => {
            const newConfig = { ...mockedConfig, id: 'mockedResponseId', name: 'Updated Name' };

            const [state] = await renderApp({
                isNewSource: false,
                config: newConfig,
                updateResource: () => HttpResponse.json(newConfig),
            });

            await waitFor(() => {
                expect(screen.getByText('Source configuration updated successfully.')).toBeVisible();
                expect(state.id).toBe(newConfig.id);
            });
        });
    });

    describe('prepareFormData', () => {
        it('awaits prepareFormData and lets bodyFormatter read its mutations to the FormData', async () => {
            const prepareFormData = async (formData: FormData) => {
                await Promise.resolve();
                formData.set('images_folder_path', '/mutated/by/prepare');
            };

            server.use(
                http.post('/api/sources', () => HttpResponse.json({ ...mockedConfig, id: 'new-id-test' })),
                http.patch('/api/projects/{project_id}/pipeline', () =>
                    HttpResponse.json({ project_id: '', status: 'idle', device: 'images_folder' })
                )
            );

            const { result } = renderHook(() =>
                useSourceAction({ config: mockedConfig, isNewSource: true, bodyFormatter, prepareFormData })
            );
            const [, submitAction] = result.current;

            const formData = new FormData();
            formData.append('name', mockedConfig.name);
            formData.append('source_type', mockedConfig.source_type);
            formData.append('images_folder_path', mockedConfig.images_folder_path);
            formData.append('ignore_existing_images', String(mockedConfig.ignore_existing_images));

            await act(async () => {
                startTransition(async () => submitAction(formData));
            });

            await waitFor(() => {
                expect(screen.getByText('Source configuration created successfully.')).toBeVisible();
                expect(result.current[0].id).toBe('new-id-test');
                expect(result.current[0].images_folder_path).toBe('/mutated/by/prepare');
            });
        });

        it('falls back to the previous state (not a partial body) and never calls bodyFormatter when prepareFormData rejects', async () => {
            const prepareFormData = async (): Promise<void> => {
                throw { detail: 'upload failed' };
            };
            const bodyFormatterSpy = vi.fn(bodyFormatter);

            const { result } = renderHook(() =>
                useSourceAction({
                    config: mockedConfig,
                    isNewSource: true,
                    bodyFormatter: bodyFormatterSpy,
                    prepareFormData,
                })
            );
            const [, submitAction] = result.current;

            await act(async () => {
                startTransition(async () => submitAction(new FormData()));
            });

            await waitFor(() => {
                expect(screen.getByText('Failed to save source configuration, upload failed')).toBeVisible();
                expect(result.current[0]).toEqual(mockedConfig);
            });

            expect(bodyFormatterSpy).not.toHaveBeenCalled();
        });
    });

    describe('video-file integration (real prepareVideoFileFormData + videoFileBodyFormatter)', () => {
        it('does not create the source when the video upload fails', async () => {
            const videoConfig: VideoFileSourceConfig = {
                id: '',
                name: 'My video source',
                source_type: 'video_file',
                video_path: '',
                loop: false,
            };
            let sourceWasCreated = false;

            server.use(
                http.post('/api/sources/media', () => {
                    // The 422 response has no documented schema in the OpenAPI spec (description only).
                    // @ts-expect-error There is an incorrect type in OpenAPI
                    return HttpResponse.json({ detail: 'Unsupported video format' }, { status: 422 });
                }),
                http.post('/api/sources', () => {
                    sourceWasCreated = true;
                    return HttpResponse.json({ ...videoConfig, id: 'should-not-be-used' });
                })
            );

            const { result } = renderHook(() =>
                useSourceAction({
                    config: videoConfig,
                    isNewSource: true,
                    bodyFormatter: videoFileBodyFormatter,
                    prepareFormData: prepareVideoFileFormData,
                })
            );
            const [, submitAction] = result.current;

            const formData = new FormData();
            formData.append('id', videoConfig.id);
            formData.append('name', videoConfig.name);
            formData.append('video_path', '');
            formData.append('video_file', new File(['fake-video-bytes'], 'sample.mp4', { type: 'video/mp4' }));
            formData.append('loop', '');

            await act(async () => {
                startTransition(async () => submitAction(formData));
            });

            await waitFor(() => {
                expect(screen.getByText('Failed to save source configuration, Unsupported video format')).toBeVisible();
            });

            expect(sourceWasCreated).toBe(false);
            expect(result.current[0]).toEqual(videoConfig);
        });
    });
});
