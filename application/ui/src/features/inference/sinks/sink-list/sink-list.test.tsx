// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { MqttSinkConfig } from '@/api/types';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { getMockedPipeline } from 'mocks/mock-pipeline';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { SinkList } from './sink-list.component';

const mqttSink: MqttSinkConfig = {
    id: 'mqtt-sink-id',
    name: 'Factory broker',
    sink_type: 'mqtt',
    broker_host: 'broker.local',
    broker_port: 1883,
    topic: 'geti/predictions',
    auth_required: false,
    rate_limit: null,
    output_formats: ['image_with_predictions'],
};

describe('SinkList', () => {
    beforeEach(() => {
        server.use(
            http.get('/api/projects/{project_id}/pipeline', () => HttpResponse.json(getMockedPipeline({ sink: null })))
        );
    });

    describe('test connection', () => {
        it.each([
            {
                scenario: 'marks a reachable sink as ready',
                body: { reachable: true, latency_ms: 5, error: null },
                status: 200,
                expectedLabel: 'Ready',
            },
            {
                scenario: 'marks an unreachable sink',
                body: { reachable: false, latency_ms: null, error: 'Timeout' },
                status: 200,
                expectedLabel: 'Unreachable',
            },
            {
                scenario: 'shows the reason when the connection test fails',
                body: { detail: 'Broker refused the connection' },
                status: 400,
                expectedLabel: 'Broker refused the connection',
            },
        ])('$scenario', async ({ body, status, expectedLabel }) => {
            server.use(http.post('/api/sinks/{sink_id}:test', () => HttpResponse.json(body as never, { status })));

            render(<SinkList sinks={[mqttSink]} onAddSink={rs.fn()} onEditSink={rs.fn()} />);

            const card = await screen.findByTestId(`sink-card-${mqttSink.name}`);
            expect(within(card).queryByText(expectedLabel)).not.toBeInTheDocument();

            await userEvent.click(within(card).getByRole('button', { name: 'sink menu' }));
            await userEvent.click(screen.getByRole('menuitem', { name: 'Test connection' }));

            expect(await within(card).findByText(expectedLabel)).toBeVisible();
        });
    });
});
