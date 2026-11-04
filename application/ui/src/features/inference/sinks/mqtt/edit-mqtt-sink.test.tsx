// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { MqttSinkConfig } from '@/api/types';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { getMockedPipeline } from 'mocks/mock-pipeline';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { EditMqttSink } from './edit-mqtt-sink.component';

const sink: MqttSinkConfig = {
    id: 'sink-id',
    name: 'Local broker',
    sink_type: 'mqtt',
    broker_host: 'localhost',
    broker_port: 1883,
    topic: 'predictions',
    auth_required: false,
    rate_limit: null,
    output_formats: ['predictions'],
};

describe('EditMqttSink', () => {
    const updateBody = rs.fn();
    const pipelineBody = rs.fn();

    beforeEach(() => {
        rs.clearAllMocks();
        server.use(
            http.patch('/api/sinks/{sink_id}', async ({ request }) => {
                updateBody(await request.json());

                return HttpResponse.json({ ...sink, name: 'Renamed' });
            }),
            http.post('/api/sinks/{sink_id}:test', () => HttpResponse.json({ reachable: true })),
            http.patch('/api/projects/{project_id}/pipeline', async ({ request }) => {
                pipelineBody(await request.json());

                return HttpResponse.json(getMockedPipeline());
            })
        );
    });

    const renderEdit = (props: { isConnected?: boolean; onSaved?: () => void } = {}) =>
        render(
            <EditMqttSink
                sink={sink}
                isConnected={props.isConnected ?? false}
                onSaved={props.onSaved ?? rs.fn()}
                onBackToList={rs.fn()}
            />
        );

    const rename = async (user: ReturnType<typeof userEvent.setup>) => {
        const name = screen.getByRole('textbox', { name: 'Name' });
        await user.clear(name);
        await user.type(name, 'Renamed');
    };

    it('"Save" patches the sink without id and sink_type and does not connect', async () => {
        const onSaved = rs.fn();
        const user = userEvent.setup();

        renderEdit({ onSaved });

        await rename(user);
        await user.click(screen.getByRole('button', { name: 'Save' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
        expect(updateBody).toHaveBeenCalledWith({
            name: 'Renamed',
            broker_host: 'localhost',
            broker_port: 1883,
            topic: 'predictions',
            auth_required: false,
            rate_limit: null,
            output_formats: ['predictions'],
        });
        expect(pipelineBody).not.toHaveBeenCalled();
    });

    it('"Save & Connect" connects the sink to the pipeline before onSaved', async () => {
        const onSaved = rs.fn();
        const user = userEvent.setup();

        renderEdit({ onSaved });

        await rename(user);
        await user.click(screen.getByRole('button', { name: 'Save & Connect' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
        expect(pipelineBody).toHaveBeenCalledWith({ sink_id: 'sink-id' });
    });

    it('hides "Save & Connect" when the sink is already connected', () => {
        renderEdit({ isConnected: true });

        expect(screen.getByRole('button', { name: 'Save' })).toBeVisible();
        expect(screen.queryByRole('button', { name: 'Save & Connect' })).not.toBeInTheDocument();
    });

    it('keeps every edited value and does not connect when saving fails', async () => {
        server.use(
            http.patch('/api/sinks/{sink_id}', () =>
                HttpResponse.json({ detail: 'Invalid topic' } as never, { status: 400 })
            )
        );
        const onSaved = rs.fn();
        const user = userEvent.setup();

        renderEdit({ onSaved });

        await rename(user);
        await user.type(screen.getByRole('textbox', { name: 'Topic' }), '/new');
        await user.click(screen.getByRole('switch', { name: 'Require Authentication' }));
        await user.click(screen.getByRole('checkbox', { name: 'Image Original' }));
        await user.click(screen.getByRole('button', { name: 'Save & Connect' }));

        expect(await screen.findByText(/Invalid topic/)).toBeVisible();
        expect(screen.getByRole('textbox', { name: 'Name' })).toHaveValue('Renamed');
        expect(screen.getByRole('textbox', { name: 'Topic' })).toHaveValue('predictions/new');
        expect(screen.getByRole('switch', { name: 'Require Authentication' })).toBeChecked();
        expect(screen.getByRole('checkbox', { name: 'Image Original' })).toBeChecked();
        expect(pipelineBody).not.toHaveBeenCalled();
        expect(onSaved).not.toHaveBeenCalled();
    });
});
