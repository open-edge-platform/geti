// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { LocalFolderSinkConfig, MqttSinkConfig, SinkConfig, WebhookSinkConfig } from '@/api/types';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { getMockedPipeline } from 'mocks/mock-pipeline';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../api/utils';
import { server } from '../../../msw-node-setup';
import { createQueryClient } from '../../../query-client/query-client';
import { Sinks } from './sinks.component';

const folderSink: LocalFolderSinkConfig = {
    id: 'folder-sink-id',
    name: 'Results folder',
    sink_type: 'folder',
    folder_path: '/data/results',
    rate_limit: 0.2,
    output_formats: ['predictions', 'image_original'],
};

const webhookSink: WebhookSinkConfig = {
    id: 'webhook-sink-id',
    name: 'Alerts webhook',
    sink_type: 'webhook',
    webhook_url: 'https://hooks.local/alerts',
    http_method: 'POST',
    headers: { Authorization: 'Bearer token' },
    timeout: 5,
    rate_limit: 2,
    output_formats: ['predictions'],
};

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

const rosSink = { id: 'ros-sink-id', name: 'Robot topic', sink_type: 'ros', topic: '/robot', output_formats: [] };

const setupHandlers = ({
    sinks,
    connectedSinkId = null,
    connectFails = false,
}: {
    sinks: unknown[];
    connectedSinkId?: string | null;
    connectFails?: boolean;
}) => {
    const state = { sinks: [...sinks] as SinkConfig[], connectedSinkId };

    server.use(
        http.get('/api/sinks', () => HttpResponse.json(state.sinks as never)),
        http.post('/api/sinks', async ({ request }) => {
            const sink = { ...(await request.json()), id: 'created-sink-id' } as SinkConfig;
            state.sinks.push(sink);

            return HttpResponse.json(sink as never, { status: 201 });
        }),
        http.post('/api/sinks/{sink_id}:test', () =>
            HttpResponse.json({ reachable: true, latency_ms: 5, error: null })
        ),
        http.get('/api/projects/{project_id}/pipeline', () =>
            HttpResponse.json(
                getMockedPipeline({ sink: state.sinks.find(({ id }) => id === state.connectedSinkId) ?? null })
            )
        ),
        http.patch('/api/projects/{project_id}/pipeline', async ({ request }) => {
            if (connectFails) {
                return HttpResponse.json({ detail: 'Pipeline is busy' } as never, { status: 409 });
            }

            state.connectedSinkId = ((await request.json()) as { sink_id: string }).sink_id;

            return HttpResponse.json(getMockedPipeline());
        })
    );

    return state;
};

const getCard = (name: string) => screen.findByTestId(`sink-card-${name}`);

const addFolderSink = async (folderPath: string) => {
    await userEvent.click(await screen.findByRole('button', { name: 'Add new sink' }));
    await userEvent.click(screen.getByRole('button', { name: /^Folder$/ }));
    await userEvent.type(await screen.findByRole('textbox', { name: /Folder Path/i }), folderPath);
    await userEvent.click(screen.getByRole('checkbox', { name: 'Predictions' }));
    await userEvent.click(screen.getByRole('button', { name: 'Add & Use' }));
};

describe('Sinks', () => {
    it('lists the supported sinks with the connected one first and hides unsupported ones', async () => {
        setupHandlers({ sinks: [folderSink, rosSink, webhookSink, mqttSink], connectedSinkId: mqttSink.id });

        render(<Sinks />);

        const mqttCard = await getCard(mqttSink.name);
        const cards = screen.getAllByTestId(/^sink-card-/);

        expect(cards.map((card) => card.dataset.testid)).toEqual([
            `sink-card-${mqttSink.name}`,
            `sink-card-${folderSink.name}`,
            `sink-card-${webhookSink.name}`,
        ]);
        expect(screen.queryByText('Robot topic')).not.toBeInTheDocument();

        expect(within(mqttCard).getByText('In use')).toBeVisible();
        expect(within(mqttCard).getByText('mqtt', { exact: true })).toBeVisible();
        expect(within(mqttCard).getByText('Broker host: broker.local')).toBeVisible();
        expect(within(mqttCard).getByText('Broker port: 1883')).toBeVisible();
        expect(within(mqttCard).getByText('Topic: geti/predictions')).toBeVisible();
        expect(within(mqttCard).getByText('Auth required: No')).toBeVisible();
        expect(within(mqttCard).getByText('Rate limit: Not set')).toBeVisible();
        expect(within(mqttCard).getByText('image with predictions', { exact: true })).toBeVisible();

        const folderCard = within(cards[1]);
        expect(folderCard.queryByText('In use')).not.toBeInTheDocument();
        expect(folderCard.getByText('folder', { exact: true })).toBeVisible();
        expect(folderCard.getByText('Folder path: /data/results')).toBeVisible();
        expect(folderCard.getByText('Rate limit: 1 sample every 5 seconds')).toBeVisible();
        expect(folderCard.getByText('predictions', { exact: true })).toBeVisible();
        expect(folderCard.getByText('image original', { exact: true })).toBeVisible();

        const webhookCard = within(cards[2]);
        expect(webhookCard.queryByText('In use')).not.toBeInTheDocument();
        expect(webhookCard.getByText('webhook', { exact: true })).toBeVisible();
        expect(webhookCard.getByText('Webhook URL: https://hooks.local/alerts')).toBeVisible();
        expect(webhookCard.getByText('HTTP method: POST')).toBeVisible();
        expect(webhookCard.getByText('Timeout: 5')).toBeVisible();
        expect(webhookCard.getByText('Rate limit: 2 samples every 1 second')).toBeVisible();
        expect(webhookCard.getByText('Authorization: Bearer token')).toBeVisible();
    });

    it('shows a created sink without a rate limit as "Rate limit: Not set" and in use', async () => {
        const state = setupHandlers({ sinks: [] });

        render(<Sinks />);

        await addFolderSink('/data/snapshots');

        const card = await getCard('Local folder sink');

        expect(state.sinks).toEqual([
            expect.objectContaining({
                folder_path: '/data/snapshots',
                rate_limit: null,
                output_formats: ['predictions'],
            }),
        ]);
        expect(within(card).getByText('Folder path: /data/snapshots')).toBeVisible();
        expect(within(card).getByText('Rate limit: Not set')).toBeVisible();
        expect(await within(card).findByText('In use')).toBeVisible();
    });

    it('lists a created sink that could not be connected as not in use', async () => {
        const queryClient = createQueryClient();
        setupHandlers({ sinks: [], connectFails: true });

        const { unmount } = render(<Sinks />, { queryClient });

        await addFolderSink('/data/snapshots');
        expect(await screen.findByText(/Pipeline is busy/)).toBeVisible();
        expect(screen.getByRole('button', { name: 'Add & Use' })).toBeVisible();

        unmount();
        render(<Sinks />, { queryClient });

        const card = await getCard('Local folder sink');
        await waitFor(() => expect(within(card).queryByText('In use')).not.toBeInTheDocument());
        expect(within(card).getByText('Folder path: /data/snapshots')).toBeVisible();
    });
});
