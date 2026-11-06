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

    it.each([
        {
            label: 'usb camera',
            config: { id: '1', name: 'My USB', source_type: 'usb_camera', device_id: 0 },
            name: 'My USB',
            assertFields: () => expect(screen.getByRole('button', { name: /Camera list/i })).toBeInTheDocument(),
        },
        {
            label: 'ip camera',
            config: {
                id: '2',
                name: 'My IP',
                source_type: 'ip_camera',
                stream_url: 'rtsp://host/stream',
                auth_required: false,
            },
            name: 'My IP',
            assertFields: () =>
                expect(screen.getByRole('textbox', { name: /Stream Url/i })).toHaveValue('rtsp://host/stream'),
        },
        {
            label: 'video file',
            config: { id: '3', name: 'My Video', source_type: 'video_file', video_path: '/data/v.mp4', loop: false },
            name: 'My Video',
            assertFields: () => {
                expect(screen.getByRole('textbox', { name: /Video file path/i })).toHaveValue('/data/v.mp4');
                expect(screen.getByTestId('upload-video-file')).toBeInTheDocument();
            },
        },
    ] as const)('renders the $label form with the saved values', async ({ config, name, assertFields }) => {
        renderForm(config);

        expect(await screen.findByRole('textbox', { name: /Name/i })).toHaveValue(name);
        assertFields();
    });
});
