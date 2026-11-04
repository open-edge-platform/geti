// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { SourceConfigPayload } from '@/api/types';
import { screen } from '@testing-library/react';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../api/utils';
import { server } from '../../../msw-node-setup';
import { EditSourceForm } from './edit-source-form.component';

describe('EditSourceForm', () => {
    beforeEach(() => {
        server.use(
            http.get('/api/system/devices/camera', () => HttpResponse.json([{ index: 0, name: 'Integrated Webcam' }]))
        );
    });

    const renderForm = (config: SourceConfigPayload) =>
        render(<EditSourceForm config={config} isConnected={false} onSaved={rs.fn()} onBackToList={rs.fn()} />);

    it('renders the usb camera form with the saved name', async () => {
        renderForm({ id: '1', name: 'My USB', source_type: 'usb_camera', device_id: 0 });

        expect(await screen.findByRole('textbox', { name: /Name/i })).toHaveValue('My USB');
        expect(screen.getByRole('button', { name: /Camera list/i })).toBeInTheDocument();
    });

    it('renders the ip camera form with the saved values', () => {
        renderForm({
            id: '2',
            name: 'My IP',
            source_type: 'ip_camera',
            stream_url: 'rtsp://host/stream',
            auth_required: false,
        });

        expect(screen.getByRole('textbox', { name: /Name/i })).toHaveValue('My IP');
        expect(screen.getByRole('textbox', { name: /Stream Url/i })).toHaveValue('rtsp://host/stream');
    });

    it('renders the video file form with the saved path', () => {
        renderForm({ id: '3', name: 'My Video', source_type: 'video_file', video_path: '/data/v.mp4', loop: false });

        expect(screen.getByRole('textbox', { name: /Name/i })).toHaveValue('My Video');
        expect(screen.getByTestId('upload-video-file')).toBeInTheDocument();
    });
});
