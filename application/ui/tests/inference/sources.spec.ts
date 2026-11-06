// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { IPCameraSourceConfig, USBCameraSourceConfig, VideoFileSourceConfig } from '@/api/types';
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

        test('adds a video file source by uploading a file', async ({ inferencePage, sourcesPage }) => {
            await inferencePage.goto();
            await sourcesPage.openAddSourceForm('Video file');

            await sourcesPage.getVideoFileInput().setInputFiles({
                name: 'sample.mp4',
                mimeType: 'video/mp4',
                buffer: Buffer.from('fake-video-bytes'),
            });
            await sourcesPage.getAddAndUseButton().click();

            const card = sourcesPage.getSourceCard('Video file source');
            await expect(card.getByText(/^Video path: \/data\/source_media\/.+\/sample\.mp4$/)).toBeVisible();
            await expect(card.getByText('In use')).toBeVisible();
        });
    });

    test.describe('source menu', () => {
        test('connects a source to the pipeline and removes another one', async ({
            inferencePage,
            sourcesPage,
            network,
        }) => {
            network.use(
                ...createPipelineBackend({ sources: [ipCamera, videoFile], pipeline: { source: videoFile } }).handlers
            );

            await inferencePage.goto();
            await sourcesPage.selectSourceMenuAction(ipCamera.name, 'Connect');

            await expect(sourcesPage.getToast(`Successfully connected to "${ipCamera.name}".`)).toBeVisible();
            await expect(sourcesPage.getSourceCard(ipCamera.name).getByText('In use')).toBeVisible();
            await expect(sourcesPage.getSourceCard(videoFile.name).getByText('In use')).toBeHidden();

            await sourcesPage.selectSourceMenuAction(videoFile.name, 'Remove');

            await expect(sourcesPage.getToast(`${videoFile.name} has been removed successfully!`)).toBeVisible();
            await expect(sourcesPage.getSourceCard(videoFile.name)).toBeHidden();
            await expect(sourcesPage.getSourceCard(ipCamera.name)).toBeVisible();
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
    });

    test.describe('editing a source', () => {
        test('edits a USB camera source, then saves and connects it', async ({
            inferencePage,
            sourcesPage,
            network,
            page,
        }) => {
            network.use(
                ...createPipelineBackend({ sources: [usbCamera, videoFile], pipeline: { source: videoFile } }).handlers
            );

            await inferencePage.goto();
            await sourcesPage.selectSourceMenuAction(usbCamera.name, 'Edit');

            await expect(page.getByText('Edit input source')).toBeVisible();

            const nameInput = sourcesPage.getNameField();
            await expect(nameInput).toHaveValue(usbCamera.name);

            await nameInput.fill('Desk camera (left)');
            await sourcesPage.getSaveButton().click();

            await expect(sourcesPage.getToast('Source configuration updated successfully.')).toBeVisible();

            const card = sourcesPage.getSourceCard('Desk camera (left)');
            await expect(card.getByText('Device: FaceTime HD Camera')).toBeVisible();
            await expect(card.getByText('In use')).toBeHidden();

            await sourcesPage.selectSourceMenuAction('Desk camera (left)', 'Edit');

            await sourcesPage.getNameField().fill('Desk camera (right)');
            await sourcesPage.getSaveAndConnectButton().click();

            const connectedCard = sourcesPage.getSourceCard('Desk camera (right)');
            await expect(connectedCard.getByText('Device: FaceTime HD Camera')).toBeVisible();
            await expect(connectedCard.getByText('In use')).toBeVisible();
            await expect(sourcesPage.getSourceCard(videoFile.name).getByText('In use')).toBeHidden();

            await sourcesPage.selectSourceMenuAction('Desk camera (right)', 'Edit');

            await expect(sourcesPage.getSaveButton()).toBeVisible();
            await expect(sourcesPage.getSaveAndConnectButton()).toBeHidden();
        });
    });
});
