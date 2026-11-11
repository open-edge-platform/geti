// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { SourceConfigPayload } from '@/api/types';
import { screen } from '@testing-library/react';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../../api/utils';
import { server } from '../../../../../msw-node-setup';
import { SourceDetails } from './source-details.component';

describe('SourceDetails', () => {
    beforeEach(() => {
        server.use(
            http.get('/api/system/devices/camera', () => HttpResponse.json([{ index: 0, name: 'Integrated Webcam' }]))
        );
    });

    it('shows the device name for a known usb camera', async () => {
        const source: SourceConfigPayload = { id: '1', name: 'Cam', source_type: 'usb_camera', device_id: 0 };

        render(<SourceDetails source={source} />);

        expect(await screen.findByText('Device: Integrated Webcam')).toBeInTheDocument();
    });

    it('shows the loading text, then an unknown device label for an unlisted usb camera', async () => {
        const source: SourceConfigPayload = { id: '1', name: 'Cam', source_type: 'usb_camera', device_id: 7 };

        render(<SourceDetails source={source} />);

        expect(screen.getByRole('listitem')).toHaveTextContent('Loading...');
        expect(await screen.findByText('Device: Unknown device (id: 7)')).toBeInTheDocument();
    });

    it.each([
        [true, 'Auth required: Yes'],
        [false, 'Auth required: No'],
    ])('shows stream url and auth for an ip camera (auth_required=%s)', (authRequired, authText) => {
        const source: SourceConfigPayload = {
            id: '2',
            name: 'IP',
            source_type: 'ip_camera',
            stream_url: 'rtsp://192.168.1.10/stream',
            auth_required: authRequired,
        };

        render(<SourceDetails source={source} />);

        expect(screen.getByText('Stream url: rtsp://192.168.1.10/stream')).toBeInTheDocument();
        expect(screen.getByText(authText)).toBeInTheDocument();
    });

    it('shows the video path for a video file', () => {
        const source: SourceConfigPayload = {
            id: '3',
            name: 'Video',
            source_type: 'video_file',
            video_path: '/data/video.mp4',
            loop: false,
        };

        render(<SourceDetails source={source} />);

        expect(screen.getByText('Video path: /data/video.mp4')).toBeInTheDocument();
    });
});
