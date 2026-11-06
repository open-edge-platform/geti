// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { SourceConfig } from '@/api/types';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { getMockedPipeline } from 'mocks/mock-pipeline';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../api/utils';
import { server } from '../../../msw-node-setup';
import * as actualWebRtc from '../stream/web-rtc-connection-provider' with { rstest: 'importActual' };
import { Sources } from './sources.component';

rs.mock('../stream/web-rtc-connection-provider', () => ({
    ...actualWebRtc,
    useWebRTCConnection: () => ({ stop: rs.fn() }),
}));

const usbCamera: SourceConfig = { id: 'usb-id', name: 'Desk camera', source_type: 'usb_camera', device_id: 1 };
const ipCamera: SourceConfig = {
    id: 'ip-id',
    name: 'Gate camera',
    source_type: 'ip_camera',
    stream_url: 'rtsp://gate.local/stream',
    auth_required: true,
};
const videoFile: SourceConfig = {
    id: 'video-id',
    name: 'Conveyor recording',
    source_type: 'video_file',
    video_path: '/videos/conveyor.mp4',
    loop: false,
};
const detachedUsbCamera: SourceConfig = {
    id: 'old-usb-id',
    name: 'Old camera',
    source_type: 'usb_camera',
    device_id: 9,
};
const disconnected: SourceConfig = { id: 'disconnected-id', name: 'No source', source_type: 'disconnected' };

const renderActions = (sources: SourceConfig[], connected: SourceConfig | null = null) => {
    server.use(
        http.get('/api/system/devices/camera', () =>
            HttpResponse.json([
                { index: 1, name: 'FaceTime HD Camera' },
                { index: 2, name: 'Logitech C920' },
            ])
        ),
        http.get('/api/sources', () => HttpResponse.json(sources)),
        http.get('/api/projects/{project_id}/pipeline', () =>
            HttpResponse.json(getMockedPipeline({ source: connected, status: 'idle' }))
        )
    );

    render(<Sources />);
};

describe('Sources', () => {
    it('lists every source type with its settings, connected source first, and hides disconnected placeholders', async () => {
        renderActions([usbCamera, ipCamera, disconnected, videoFile, detachedUsbCamera], videoFile);

        await screen.findAllByTestId(/^source-card-/);
        const cards = screen.getAllByTestId(/^source-card-/);

        expect(cards).toHaveLength(4);
        expect(cards[0]).toHaveAttribute('data-testid', `source-card-${videoFile.name}`);
        expect(screen.queryByTestId(`source-card-${disconnected.name}`)).not.toBeInTheDocument();

        const videoCard = within(screen.getByTestId(`source-card-${videoFile.name}`));
        expect(videoCard.getByText('video file', { exact: true })).toBeVisible();
        expect(videoCard.getByText('In use')).toBeVisible();
        expect(videoCard.getByText('Video path: /videos/conveyor.mp4')).toBeVisible();

        const usbCard = within(screen.getByTestId(`source-card-${usbCamera.name}`));
        expect(usbCard.getByText('usb camera', { exact: true })).toBeVisible();
        expect(await usbCard.findByText('Device: FaceTime HD Camera')).toBeVisible();
        expect(usbCard.queryByText('In use')).not.toBeInTheDocument();

        const ipCard = within(screen.getByTestId(`source-card-${ipCamera.name}`));
        expect(ipCard.getByText('ip camera', { exact: true })).toBeVisible();
        expect(ipCard.getByText('Stream url: rtsp://gate.local/stream')).toBeVisible();
        expect(ipCard.getByText('Auth required: Yes')).toBeVisible();
        expect(ipCard.queryByText('In use')).not.toBeInTheDocument();

        const detachedCard = within(screen.getByTestId(`source-card-${detachedUsbCamera.name}`));
        expect(await detachedCard.findByText('Device: Unknown device (id: 9)')).toBeVisible();
    });

    it('suggests a unique default name when the default one is taken', async () => {
        renderActions([{ ...ipCamera, name: 'IP camera source' }]);

        await userEvent.click(await screen.findByRole('button', { name: 'Add new source' }));
        await userEvent.click(screen.getByRole('button', { name: 'IP Camera' }));

        expect(await screen.findByRole('textbox', { name: 'Name' })).toHaveValue('IP camera source (1)');
    });
});
