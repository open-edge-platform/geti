// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { IPCameraSourceConfig, SourceConfig, USBCameraSourceConfig, VideoFileSourceConfig } from '@/api/types';
import { HttpResponse } from 'msw';

import { expect, http, test } from '../fixtures';
import { createPipelineBackend } from './pipeline-backend';

const usbCamera: USBCameraSourceConfig = {
    id: 'usb-camera-id',
    name: 'Desk camera',
    source_type: 'usb_camera',
    device_id: 1,
};

const ipCamera: IPCameraSourceConfig = {
    id: 'ip-camera-id',
    name: 'Gate camera',
    source_type: 'ip_camera',
    stream_url: 'rtsp://gate.local/stream',
    auth_required: true,
};

const videoFile: VideoFileSourceConfig = {
    id: 'video-file-id',
    name: 'Conveyor recording',
    source_type: 'video_file',
    video_path: '/videos/conveyor.mp4',
    loop: false,
};

const disconnected: SourceConfig = { id: 'disconnected-id', name: 'No source', source_type: 'disconnected' };

const cameraDevices = [
    { index: 1, name: 'FaceTime HD Camera' },
    { index: 2, name: 'Logitech C920' },
];

test.describe('Pipeline sources', () => {
    test.beforeEach(({ network }) => {
        network.use(http.get('/api/system/devices/camera', () => HttpResponse.json(cameraDevices)));
    });

    test.describe('adding a source', () => {
        test.beforeEach(({ network }) => {
            network.use(...createPipelineBackend().handlers);
        });

        test('adds a USB camera source and connects it to the pipeline', async ({ inferencePage, sourcesPage }) => {
            await inferencePage.goto();
            await sourcesPage.openAddSourceForm('USB Camera');

            await expect(sourcesPage.getNameField()).toHaveValue('USB camera source');

            await sourcesPage.getNameField().fill('Bench camera');
            await sourcesPage.selectCamera('Logitech C920');
            await sourcesPage.getAddAndUseButton().click();

            await expect(sourcesPage.getToast('Source configuration created successfully.')).toBeVisible();

            const card = sourcesPage.getSourceCard('Bench camera');
            await expect(card.getByText('usb camera', { exact: true })).toBeVisible();
            await expect(card.getByText('Device: Logitech C920')).toBeVisible();
            await expect(card.getByText('In use')).toBeVisible();
        });

        test('does not add a USB camera source without a camera', async ({ inferencePage, sourcesPage, network }) => {
            network.use(http.get('/api/system/devices/camera', () => HttpResponse.json([])));

            await inferencePage.goto();
            await sourcesPage.openAddSourceForm('USB Camera');

            await expect(sourcesPage.getAddAndUseButton()).toBeDisabled();

            await sourcesPage.openSourceList();
            await expect(sourcesPage.getSourceCards()).toHaveCount(0);
        });

        test('lists a camera attached after refreshing the camera list', async ({
            inferencePage,
            sourcesPage,
            network,
            page,
        }) => {
            let attachedCameras = cameraDevices.slice(0, 1);
            network.use(http.get('/api/system/devices/camera', () => HttpResponse.json(attachedCameras)));

            await inferencePage.goto();
            await sourcesPage.openAddSourceForm('USB Camera');

            await page.getByRole('button', { name: 'Camera list' }).click();
            await expect(page.getByRole('option')).toHaveText(['FaceTime HD Camera']);
            await page.keyboard.press('Escape');

            attachedCameras = cameraDevices;
            await page.getByRole('button', { name: 'Refresh Cameras' }).click();

            await page.getByRole('button', { name: 'Camera list' }).click();
            await expect(page.getByRole('option')).toHaveText(['FaceTime HD Camera', 'Logitech C920']);

            await page.getByRole('option', { name: 'Logitech C920' }).click();
            await sourcesPage.getAddAndUseButton().click();

            await expect(
                sourcesPage.getSourceCard('USB camera source').getByText('Device: Logitech C920')
            ).toBeVisible();
        });

        test('adds an IP camera source that requires authentication', async ({ inferencePage, sourcesPage, page }) => {
            await inferencePage.goto();
            await sourcesPage.openAddSourceForm('IP Camera');

            await expect(sourcesPage.getNameField()).toHaveValue('IP camera source');

            await page.getByRole('textbox', { name: /Stream Url/ }).fill('rtsp://door.local/stream');
            await page.getByRole('switch', { name: 'Require Authentication' }).click();
            await sourcesPage.getAddAndUseButton().click();

            const card = sourcesPage.getSourceCard('IP camera source');
            await expect(card.getByText('ip camera', { exact: true })).toBeVisible();
            await expect(card.getByText('Stream url: rtsp://door.local/stream')).toBeVisible();
            await expect(card.getByText('Auth required: Yes')).toBeVisible();
            await expect(card.getByText('In use')).toBeVisible();
        });

        test('does not add an IP camera source without a stream URL', async ({ inferencePage, sourcesPage }) => {
            await inferencePage.goto();
            await sourcesPage.openAddSourceForm('IP Camera');

            await expect(sourcesPage.getAddAndUseButton()).toBeDisabled();

            await sourcesPage.openSourceList();
            await expect(sourcesPage.getSourceCards()).toHaveCount(0);
        });

        test('adds a looping video file source from a typed path', async ({ inferencePage, sourcesPage, page }) => {
            await inferencePage.goto();
            await sourcesPage.openAddSourceForm('Video file');

            await expect(sourcesPage.getNameField()).toHaveValue('Video file source');

            await page.getByRole('textbox', { name: /Video file path/ }).fill('/videos/parking.mp4');
            await page.getByRole('switch', { name: 'loop video' }).click();
            await sourcesPage.getAddAndUseButton().click();

            await expect(sourcesPage.getToast('Source configuration created successfully.')).toBeVisible();

            const card = sourcesPage.getSourceCard('Video file source');
            await expect(card.getByText('video file', { exact: true })).toBeVisible();
            await expect(card.getByText('Video path: /videos/parking.mp4')).toBeVisible();
            await expect(card.getByText('In use')).toBeVisible();

            await sourcesPage.selectSourceMenuAction('Video file source', 'Edit');
            await expect(page.getByRole('switch', { name: 'loop video' })).toBeChecked();
        });

        test('does not add a video file source without a path or a file', async ({ inferencePage, sourcesPage }) => {
            await inferencePage.goto();
            await sourcesPage.openAddSourceForm('Video file');

            await expect(sourcesPage.getAddAndUseButton()).toBeDisabled();

            await sourcesPage.openSourceList();
            await expect(sourcesPage.getSourceCards()).toHaveCount(0);
        });

        test('adds a video file source by uploading a file', async ({ inferencePage, sourcesPage, page }) => {
            await inferencePage.goto();
            await sourcesPage.openAddSourceForm('Video file');

            await sourcesPage.getVideoFileInput().setInputFiles({
                name: 'sample.mp4',
                mimeType: 'video/mp4',
                buffer: Buffer.from('fake-video-bytes'),
            });

            await expect(page.getByText('Selected: sample.mp4')).toBeVisible();
            await expect(page.getByRole('textbox', { name: /Video file path/ })).toHaveValue('');

            await sourcesPage.getAddAndUseButton().click();

            const card = sourcesPage.getSourceCard('Video file source');
            await expect(card.getByText(/^Video path: \/data\/source_media\/.+\/sample\.mp4$/)).toBeVisible();
            await expect(card.getByText('In use')).toBeVisible();
        });

        test('deletes the uploaded video when the source cannot be created', async ({
            inferencePage,
            sourcesPage,
            network,
        }) => {
            const deletedSourceMediaIds: string[] = [];

            network.use(
                http.post('/api/sources', () => {
                    // @ts-expect-error The 409 response has no documented schema in the OpenAPI spec.
                    return HttpResponse.json({ detail: 'Name already in use' }, { status: 409 });
                }),
                http.delete('/api/sources/media/{source_media_id}', ({ params }) => {
                    deletedSourceMediaIds.push(params.source_media_id);

                    return HttpResponse.json({ deleted_video_path: '' });
                })
            );

            await inferencePage.goto();
            await sourcesPage.openAddSourceForm('Video file');
            await sourcesPage.getVideoFileInput().setInputFiles({
                name: 'sample.mp4',
                mimeType: 'video/mp4',
                buffer: Buffer.from('fake-video-bytes'),
            });
            await sourcesPage.getAddAndUseButton().click();

            await expect(
                sourcesPage.getToast('Failed to save source configuration, Name already in use')
            ).toBeVisible();
            await expect(sourcesPage.getAddAndUseButton()).toBeVisible();
            await expect.poll(() => deletedSourceMediaIds).toHaveLength(1);
        });

        test('keeps the selected video file after a failed save and uploads it again on retry', async ({
            inferencePage,
            sourcesPage,
            network,
            page,
        }) => {
            network.use(
                http.post(
                    '/api/sources',
                    () => {
                        // @ts-expect-error The 409 response has no documented schema in the OpenAPI spec.
                        return HttpResponse.json({ detail: 'Name already in use' }, { status: 409 });
                    },
                    { once: true }
                )
            );

            await inferencePage.goto();
            await sourcesPage.openAddSourceForm('Video file');
            await sourcesPage.getVideoFileInput().setInputFiles({
                name: 'sample.mp4',
                mimeType: 'video/mp4',
                buffer: Buffer.from('fake-video-bytes'),
            });
            await sourcesPage.getAddAndUseButton().click();

            await expect(
                sourcesPage.getToast('Failed to save source configuration, Name already in use')
            ).toBeVisible();
            await expect(page.getByText('Selected: sample.mp4')).toBeVisible();

            await sourcesPage.getAddAndUseButton().click();

            await expect(
                sourcesPage
                    .getSourceCard('Video file source')
                    .getByText(/^Video path: \/data\/source_media\/.+\/sample\.mp4$/)
            ).toBeVisible();
        });

        test('keeps the form open when the new source cannot be connected', async ({
            inferencePage,
            sourcesPage,
            network,
            page,
        }) => {
            network.use(
                http.patch('/api/projects/{project_id}/pipeline', () => {
                    // @ts-expect-error The 409 response has no documented schema in the OpenAPI spec.
                    return HttpResponse.json({ detail: 'Pipeline is busy' }, { status: 409 });
                })
            );

            await inferencePage.goto();
            await sourcesPage.openAddSourceForm('IP Camera');
            await page.getByRole('textbox', { name: /Stream Url/ }).fill('rtsp://door.local/stream');
            await sourcesPage.getAddAndUseButton().click();

            await expect(sourcesPage.getToast('Source configuration created successfully.')).toBeVisible();
            await expect(sourcesPage.getToast('Pipeline is busy').first()).toBeVisible();
            await expect(sourcesPage.getAddAndUseButton()).toBeVisible();
            await expect(sourcesPage.getNameField()).toBeVisible();
            await expect(page.getByRole('textbox', { name: /Stream Url/ })).toBeVisible();
            await expect(sourcesPage.getSourceCards()).toHaveCount(0);

            await sourcesPage.openSourceList();
            await expect(sourcesPage.getSourceCard('IP camera source').getByText('In use')).toBeHidden();
        });

        test('shows the error and keeps the entered values when saving fails', async ({
            inferencePage,
            sourcesPage,
            network,
            page,
        }) => {
            network.use(
                http.post('/api/sources', () => {
                    // @ts-expect-error The 400 response has no documented schema in the OpenAPI spec.
                    return HttpResponse.json({ detail: 'Stream URL is not reachable' }, { status: 400 });
                })
            );

            await inferencePage.goto();
            await sourcesPage.openAddSourceForm('IP Camera');
            await sourcesPage.getNameField().fill('Door camera');
            await page.getByRole('textbox', { name: /Stream Url/ }).fill('rtsp://door.local/stream');
            await page.getByRole('switch', { name: 'Require Authentication' }).click();
            await sourcesPage.getAddAndUseButton().click();

            await expect(
                sourcesPage.getToast('Failed to save source configuration, Stream URL is not reachable')
            ).toBeVisible();
            await expect(sourcesPage.getNameField()).toHaveValue('Door camera');
            await expect(page.getByRole('textbox', { name: /Stream Url/ })).toHaveValue('rtsp://door.local/stream');
            await expect(page.getByRole('switch', { name: 'Require Authentication' })).toBeChecked();

            await sourcesPage.openSourceList();
            await expect(sourcesPage.getSourceCards()).toHaveCount(0);
        });
    });

    test('suggests a unique default name when the default one is taken', async ({
        inferencePage,
        sourcesPage,
        network,
    }) => {
        network.use(
            ...createPipelineBackend({
                sources: [{ ...ipCamera, name: 'IP camera source' }],
            }).handlers
        );

        await inferencePage.goto();
        await sourcesPage.openAddSourceForm('IP Camera');

        await expect(sourcesPage.getNameField()).toHaveValue('IP camera source (1)');
    });

    test('lists every source type with its settings, connected source first', async ({
        inferencePage,
        sourcesPage,
        network,
    }) => {
        const detachedUsbCamera: USBCameraSourceConfig = {
            ...usbCamera,
            id: 'detached-usb-camera-id',
            name: 'Old camera',
            device_id: 9,
        };

        network.use(
            ...createPipelineBackend({
                sources: [usbCamera, ipCamera, disconnected, videoFile, detachedUsbCamera],
                pipeline: { source: videoFile },
            }).handlers
        );

        await inferencePage.goto();

        await expect(sourcesPage.getSourceCards()).toHaveCount(4);
        await expect(sourcesPage.getSourceCards().first()).toHaveAttribute(
            'data-testid',
            `source-card-${videoFile.name}`
        );
        await expect(sourcesPage.getSourceCard(disconnected.name)).toBeHidden();

        const videoCard = sourcesPage.getSourceCard(videoFile.name);
        await expect(videoCard.getByText('In use')).toBeVisible();
        await expect(videoCard.getByText('Video path: /videos/conveyor.mp4')).toBeVisible();

        const usbCard = sourcesPage.getSourceCard(usbCamera.name);
        await expect(usbCard.getByText('Device: FaceTime HD Camera')).toBeVisible();
        await expect(usbCard.getByText('In use')).toBeHidden();

        const ipCard = sourcesPage.getSourceCard(ipCamera.name);
        await expect(ipCard.getByText('Stream url: rtsp://gate.local/stream')).toBeVisible();
        await expect(ipCard.getByText('Auth required: Yes')).toBeVisible();

        await expect(
            sourcesPage.getSourceCard(detachedUsbCamera.name).getByText('Device: Unknown device (id: 9)')
        ).toBeVisible();
    });

    test.describe('source menu', () => {
        test('connects a source to the pipeline', async ({ inferencePage, sourcesPage, network }) => {
            network.use(
                ...createPipelineBackend({ sources: [ipCamera, videoFile], pipeline: { source: videoFile } }).handlers
            );

            await inferencePage.goto();
            await sourcesPage.selectSourceMenuAction(ipCamera.name, 'Connect');

            await expect(sourcesPage.getToast(`Successfully connected to "${ipCamera.name}".`)).toBeVisible();
            await expect(sourcesPage.getSourceCard(ipCamera.name).getByText('In use')).toBeVisible();
            await expect(sourcesPage.getSourceCard(videoFile.name).getByText('In use')).toBeHidden();
        });

        test('disconnects a source right away while the pipeline is idle', async ({
            inferencePage,
            sourcesPage,
            network,
            page,
        }) => {
            network.use(
                ...createPipelineBackend({ sources: [ipCamera], pipeline: { source: ipCamera, status: 'idle' } })
                    .handlers
            );

            await inferencePage.goto();
            await sourcesPage.selectSourceMenuAction(ipCamera.name, 'Disconnect');

            await expect(page.getByRole('dialog')).toBeHidden();
            await expect(sourcesPage.getToast(`Successfully disconnected from "${ipCamera.name}".`)).toBeVisible();
            await expect(sourcesPage.getSourceCard(ipCamera.name).getByText('In use')).toBeHidden();
        });

        test('asks to confirm disconnecting from a running pipeline and disables it once confirmed', async ({
            inferencePage,
            sourcesPage,
            network,
            page,
        }) => {
            network.use(
                ...createPipelineBackend({ sources: [ipCamera], pipeline: { source: ipCamera, status: 'running' } })
                    .handlers
            );

            await inferencePage.goto();
            await expect(inferencePage.getPipelineSwitch('enabled')).toBeVisible();

            const dialog = page.getByRole('dialog');
            const card = sourcesPage.getSourceCard(ipCamera.name);

            await sourcesPage.selectSourceMenuAction(ipCamera.name, 'Disconnect');
            await expect(dialog.getByRole('heading', { name: `Disconnect ${ipCamera.name}` })).toBeVisible();
            await dialog.getByRole('button', { name: 'Cancel' }).click();

            await expect(dialog).toBeHidden();
            await expect(inferencePage.getPipelineSwitch('enabled')).toBeVisible();
            await expect(card.getByText('In use')).toBeVisible();

            await sourcesPage.selectSourceMenuAction(ipCamera.name, 'Disconnect');
            await dialog.getByRole('button', { name: 'Disconnect' }).click();

            await expect(
                sourcesPage.getToast(`Successfully disabled pipeline and disconnected from "${ipCamera.name}".`)
            ).toBeVisible();
            await expect(dialog).toBeHidden();
            await expect(inferencePage.getPipelineSwitch('disabled')).toBeVisible();
            await expect(card.getByText('In use')).toBeHidden();
        });

        test('does not allow removing or testing the connected source', async ({
            inferencePage,
            sourcesPage,
            network,
        }) => {
            network.use(...createPipelineBackend({ sources: [ipCamera], pipeline: { source: ipCamera } }).handlers);

            await inferencePage.goto();
            await sourcesPage.openSourceMenu(ipCamera.name);

            await expect(sourcesPage.getMenuItem('Remove')).toBeDisabled();
            await expect(sourcesPage.getMenuItem('Test connection')).toBeDisabled();
            await expect(sourcesPage.getMenuItem('Connect')).toBeHidden();
        });

        test('removes a source', async ({ inferencePage, sourcesPage, network }) => {
            network.use(...createPipelineBackend({ sources: [ipCamera, videoFile] }).handlers);

            await inferencePage.goto();
            await sourcesPage.selectSourceMenuAction(ipCamera.name, 'Remove');

            await expect(sourcesPage.getToast(`${ipCamera.name} has been removed successfully!`)).toBeVisible();
            await expect(sourcesPage.getSourceCard(ipCamera.name)).toBeHidden();
            await expect(sourcesPage.getSourceCard(videoFile.name)).toBeVisible();
        });

        test('marks a reachable source as ready', async ({ inferencePage, sourcesPage, network }) => {
            network.use(...createPipelineBackend({ sources: [ipCamera] }).handlers);

            await inferencePage.goto();

            const card = sourcesPage.getSourceCard(ipCamera.name);
            await expect(card).toBeVisible();
            await expect(card.getByText('Ready')).toBeHidden();

            await sourcesPage.selectSourceMenuAction(ipCamera.name, 'Test connection');

            await expect(card.getByText('Ready')).toBeVisible();
        });

        test('marks an unreachable source', async ({ inferencePage, sourcesPage, network }) => {
            network.use(...createPipelineBackend({ sources: [ipCamera] }).handlers);
            network.use(
                http.post('/api/sources/{source_id}:test', () =>
                    HttpResponse.json({ reachable: false, latency_ms: null, error: 'Timeout' })
                )
            );

            await inferencePage.goto();
            await sourcesPage.selectSourceMenuAction(ipCamera.name, 'Test connection');

            await expect(sourcesPage.getSourceCard(ipCamera.name).getByText('Unreachable')).toBeVisible();
        });

        test('shows the reason when the connection test fails', async ({ inferencePage, sourcesPage, network }) => {
            network.use(...createPipelineBackend({ sources: [ipCamera] }).handlers);
            network.use(
                http.post('/api/sources/{source_id}:test', () => {
                    // @ts-expect-error The 400 response has no documented schema in the OpenAPI spec.
                    return HttpResponse.json({ detail: 'Camera refused the connection' }, { status: 400 });
                })
            );

            await inferencePage.goto();
            await sourcesPage.selectSourceMenuAction(ipCamera.name, 'Test connection');

            await expect(
                sourcesPage.getSourceCard(ipCamera.name).getByText('Camera refused the connection')
            ).toBeVisible();
        });
    });

    test.describe('editing a source', () => {
        const editCases = [
            {
                source: usbCamera,
                field: { role: 'textbox', name: 'Name', value: usbCamera.name },
                newValue: 'Desk camera (left)',
                expectedCardName: 'Desk camera (left)',
                expectedSetting: 'Device: FaceTime HD Camera',
            },
            {
                source: ipCamera,
                field: { role: 'textbox', name: /Stream Url/, value: ipCamera.stream_url },
                newValue: 'rtsp://gate.local/hd',
                expectedCardName: ipCamera.name,
                expectedSetting: 'Stream url: rtsp://gate.local/hd',
            },
            {
                source: videoFile,
                field: { role: 'textbox', name: /Video file path/, value: videoFile.video_path },
                newValue: '/videos/conveyor-night.mp4',
                expectedCardName: videoFile.name,
                expectedSetting: 'Video path: /videos/conveyor-night.mp4',
            },
        ] as const;

        for (const { source, field, newValue, expectedCardName, expectedSetting } of editCases) {
            test(`edits a ${source.source_type} source`, async ({ inferencePage, sourcesPage, network, page }) => {
                network.use(...createPipelineBackend({ sources: [source] }).handlers);

                await inferencePage.goto();
                await sourcesPage.selectSourceMenuAction(source.name, 'Edit');

                await expect(page.getByText('Edit input source')).toBeVisible();

                const input = page.getByRole(field.role, { name: field.name, exact: true });
                await expect(input).toHaveValue(field.value);

                await input.fill(newValue);
                await sourcesPage.getSaveButton().click();

                await expect(sourcesPage.getToast('Source configuration updated successfully.')).toBeVisible();

                const card = sourcesPage.getSourceCard(expectedCardName);
                await expect(card.getByText(expectedSetting)).toBeVisible();
                await expect(card.getByText('In use')).toBeHidden();
            });
        }

        test('switches the camera of a USB camera source', async ({ inferencePage, sourcesPage, network, page }) => {
            network.use(...createPipelineBackend({ sources: [usbCamera] }).handlers);

            await inferencePage.goto();
            await sourcesPage.selectSourceMenuAction(usbCamera.name, 'Edit');

            const cameraPicker = page.getByRole('button', { name: 'Camera list' });
            await expect(cameraPicker).toHaveText('FaceTime HD Camera');

            await sourcesPage.selectCamera('Logitech C920');
            await expect(cameraPicker).toHaveText('Logitech C920');
            await sourcesPage.getSaveButton().click();

            await expect(sourcesPage.getToast('Source configuration updated successfully.')).toBeVisible();
            const card = sourcesPage.getSourceCard(usbCamera.name);
            await expect(card.getByText('Device: Logitech C920')).toBeVisible();
            await expect(card.getByText('Device: FaceTime HD Camera')).toBeHidden();
        });

        test('replaces the video of a video file source by uploading a file', async ({
            inferencePage,
            sourcesPage,
            network,
        }) => {
            network.use(...createPipelineBackend({ sources: [videoFile] }).handlers);

            await inferencePage.goto();
            await sourcesPage.selectSourceMenuAction(videoFile.name, 'Edit');

            await sourcesPage.getVideoFileInput().setInputFiles({
                name: 'sample.mp4',
                mimeType: 'video/mp4',
                buffer: Buffer.from('fake-video-bytes'),
            });
            await sourcesPage.getSaveButton().click();

            await expect(sourcesPage.getToast('Source configuration updated successfully.')).toBeVisible();
            await expect(
                sourcesPage
                    .getSourceCard(videoFile.name)
                    .getByText(/^Video path: \/data\/source_media\/.+\/sample\.mp4$/)
            ).toBeVisible();
        });

        test('saves and connects an edited source, then offers only "Save" for it', async ({
            inferencePage,
            sourcesPage,
            network,
            page,
        }) => {
            network.use(
                ...createPipelineBackend({ sources: [ipCamera, videoFile], pipeline: { source: videoFile } }).handlers
            );

            await inferencePage.goto();
            await sourcesPage.selectSourceMenuAction(ipCamera.name, 'Edit');

            await page.getByRole('switch', { name: 'Require Authentication' }).click();
            await sourcesPage.getSaveAndConnectButton().click();

            const card = sourcesPage.getSourceCard(ipCamera.name);
            await expect(card.getByText('Auth required: No')).toBeVisible();
            await expect(card.getByText('In use')).toBeVisible();

            await sourcesPage.selectSourceMenuAction(ipCamera.name, 'Edit');

            await expect(sourcesPage.getSaveButton()).toBeVisible();
            await expect(sourcesPage.getSaveAndConnectButton()).toBeHidden();
        });

        test('shows the error and keeps the edited values when updating fails', async ({
            inferencePage,
            sourcesPage,
            network,
            page,
        }) => {
            network.use(...createPipelineBackend({ sources: [ipCamera] }).handlers);
            network.use(
                http.patch('/api/sources/{source_id}', () => {
                    // @ts-expect-error The 400 response has no documented schema in the OpenAPI spec.
                    return HttpResponse.json({ detail: 'Invalid stream URL' }, { status: 400 });
                })
            );

            await inferencePage.goto();
            await sourcesPage.selectSourceMenuAction(ipCamera.name, 'Edit');
            await page.getByRole('textbox', { name: /Stream Url/ }).fill('not-a-url');
            await sourcesPage.getSaveButton().click();

            await expect(sourcesPage.getToast('Failed to save source configuration, Invalid stream URL')).toBeVisible();
            await expect(page.getByText('Edit input source')).toBeVisible();
            await expect(page.getByRole('textbox', { name: /Stream Url/ })).toHaveValue('not-a-url');
        });
    });
});
