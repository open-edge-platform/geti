// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen } from '@testing-library/react';
import { render } from 'test-utils/render';

import type { SupportedSinkConfig } from '../../types';
import { SettingsList } from './settings-list.component';

describe('SettingsList', () => {
    it('shows folder path, rate limit and output formats for a folder sink', () => {
        const sink: SupportedSinkConfig = {
            id: '1',
            name: 'Folder',
            sink_type: 'folder',
            folder_path: '/data/results',
            rate_limit: 0.2,
            output_formats: ['predictions', 'image_original'],
        };

        render(<SettingsList sink={sink} />);

        expect(screen.getByText('Folder path: /data/results')).toBeInTheDocument();
        expect(screen.getByText('Rate limit: 1 sample every 5 seconds')).toBeInTheDocument();
        expect(screen.getByText('predictions')).toBeInTheDocument();
        expect(screen.getByText('image original')).toBeInTheDocument();
    });

    it('shows request settings, headers and output formats for a webhook sink', () => {
        const sink: SupportedSinkConfig = {
            id: '2',
            name: 'Webhook',
            sink_type: 'webhook',
            webhook_url: 'https://hooks.local/alerts',
            http_method: 'POST',
            headers: { Authorization: 'Bearer token' },
            timeout: 5,
            rate_limit: 2,
            output_formats: ['image_with_predictions'],
        };

        render(<SettingsList sink={sink} />);

        expect(screen.getByText('Rate limit: 2 samples every 1 second')).toBeInTheDocument();
        expect(screen.getByText('HTTP method: POST')).toBeInTheDocument();
        expect(screen.getByText('Timeout: 5')).toBeInTheDocument();
        expect(screen.getByText('Webhook URL: https://hooks.local/alerts')).toBeInTheDocument();
        expect(screen.getByText('Authorization: Bearer token')).toBeInTheDocument();
        expect(screen.getByText('image with predictions')).toBeInTheDocument();
    });

    it.each([
        [true, 'Auth required: Yes'],
        [false, 'Auth required: No'],
    ])('shows broker settings for an mqtt sink (auth_required=%s)', (authRequired, authText) => {
        const sink: SupportedSinkConfig = {
            id: '3',
            name: 'MQTT',
            sink_type: 'mqtt',
            broker_host: 'broker.local',
            broker_port: 1883,
            topic: 'geti/predictions',
            auth_required: authRequired,
            rate_limit: null,
            output_formats: ['predictions'],
        };

        render(<SettingsList sink={sink} />);

        expect(screen.getByText('Topic: geti/predictions')).toBeInTheDocument();
        expect(screen.getByText('Rate limit: Not set')).toBeInTheDocument();
        expect(screen.getByText(authText)).toBeInTheDocument();
        expect(screen.getByText('Broker host: broker.local')).toBeInTheDocument();
        expect(screen.getByText('Broker port: 1883')).toBeInTheDocument();
    });
});
