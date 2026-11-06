// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { SinkConfig } from '@/api/types';
import { screen } from '@testing-library/react';
import { render } from 'test-utils/render';

import { EditSinkForm } from './edit-sink-form.component';

describe('EditSinkForm', () => {
    const renderForm = (config: SinkConfig) =>
        render(<EditSinkForm config={config} isConnected={false} onSaved={rs.fn()} onBackToList={rs.fn()} />);

    it.each<{ type: string; config: SinkConfig; fieldName: RegExp; fieldValue: string }>([
        {
            type: 'folder',
            config: {
                id: '1',
                name: 'My Folder',
                sink_type: 'folder',
                folder_path: '/data/output',
                rate_limit: null,
                output_formats: [],
            },
            fieldName: /Folder Path/i,
            fieldValue: '/data/output',
        },
        {
            type: 'webhook',
            config: {
                id: '2',
                name: 'My Webhook',
                sink_type: 'webhook',
                webhook_url: 'https://example.com/hook',
                http_method: 'POST',
                headers: {},
                timeout: 5,
                rate_limit: null,
                output_formats: [],
            },
            fieldName: /Webhook URL/i,
            fieldValue: 'https://example.com/hook',
        },
        {
            type: 'mqtt',
            config: {
                id: '3',
                name: 'My MQTT',
                sink_type: 'mqtt',
                broker_host: 'broker.local',
                broker_port: 1883,
                topic: 'geti/out',
                auth_required: false,
                rate_limit: null,
                output_formats: [],
            },
            fieldName: /Broker Host/i,
            fieldValue: 'broker.local',
        },
    ])('renders the $type form with the saved values', ({ config, fieldName, fieldValue }) => {
        renderForm(config);

        expect(screen.getByRole('textbox', { name: /Name/i })).toHaveValue(config.name);
        expect(screen.getByRole('textbox', { name: fieldName })).toHaveValue(fieldValue);
    });
});
