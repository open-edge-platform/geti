// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { SinkConfig } from '@/api/types';
import { screen } from '@testing-library/react';
import { render } from 'test-utils/render';

import { EditSinkForm } from './edit-sink-form.component';

describe('EditSinkForm', () => {
    const renderForm = (config: SinkConfig) =>
        render(<EditSinkForm config={config} isConnected={false} onSaved={rs.fn()} onBackToList={rs.fn()} />);

    it('renders the folder form with the saved values', () => {
        renderForm({
            id: '1',
            name: 'My Folder',
            sink_type: 'folder',
            folder_path: '/data/output',
            rate_limit: null,
            output_formats: [],
        });

        expect(screen.getByRole('textbox', { name: /Name/i })).toHaveValue('My Folder');
        expect(screen.getByRole('textbox', { name: /Folder Path/i })).toHaveValue('/data/output');
    });

    it('renders the webhook form with the saved values', () => {
        renderForm({
            id: '2',
            name: 'My Webhook',
            sink_type: 'webhook',
            webhook_url: 'https://example.com/hook',
            http_method: 'POST',
            headers: {},
            timeout: 5,
            rate_limit: null,
            output_formats: [],
        });

        expect(screen.getByRole('textbox', { name: /Name/i })).toHaveValue('My Webhook');
        expect(screen.getByRole('textbox', { name: /Webhook URL/i })).toHaveValue('https://example.com/hook');
    });

    it('renders the mqtt form with the saved values', () => {
        renderForm({
            id: '3',
            name: 'My MQTT',
            sink_type: 'mqtt',
            broker_host: 'broker.local',
            broker_port: 1883,
            topic: 'geti/out',
            auth_required: false,
            rate_limit: null,
            output_formats: [],
        });

        expect(screen.getByRole('textbox', { name: /Name/i })).toHaveValue('My MQTT');
        expect(screen.getByRole('textbox', { name: /Broker Host/i })).toHaveValue('broker.local');
    });
});
