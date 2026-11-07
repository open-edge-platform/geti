// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { getMockedPipeline } from 'mocks/mock-pipeline';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { AddMqttSink } from './add-mqtt-sink.component';

const createdSink = {
    id: 'new-sink-id',
    name: 'My broker',
    sink_type: 'mqtt' as const,
    broker_host: 'localhost',
    broker_port: 1883,
    topic: 'predictions',
    auth_required: true,
    rate_limit: null,
    output_formats: ['predictions' as const],
};

const fillForm = async (user: ReturnType<typeof userEvent.setup>) => {
    const name = screen.getByRole('textbox', { name: 'Name' });
    await user.clear(name);
    await user.type(name, 'My broker');
    await user.type(screen.getByRole('textbox', { name: /Broker Host/i }), 'localhost');
    await user.type(screen.getByRole('textbox', { name: 'Topic' }), 'predictions');
    await user.click(screen.getByRole('switch', { name: 'Require Authentication' }));
    await user.click(screen.getByRole('checkbox', { name: 'Predictions' }));
};

describe('AddMqttSink', () => {
    beforeEach(() => {
        server.use(http.post('/api/sinks/{sink_id}:test', () => HttpResponse.json({ reachable: true })));
    });

    it('disables "Add & Use" until Broker Host and an output format are provided', async () => {
        render(<AddMqttSink onSaved={rs.fn()} />);

        expect(screen.getByRole('button', { name: 'Add & Use' })).toBeDisabled();

        await userEvent.type(screen.getByRole('textbox', { name: /Broker Host/i }), 'localhost');
        expect(screen.getByRole('button', { name: 'Add & Use' })).toBeDisabled();

        await userEvent.click(screen.getByRole('checkbox', { name: 'Predictions' }));
        expect(screen.getByRole('button', { name: 'Add & Use' })).toBeEnabled();
    });

    it('creates the sink without id, connects it to the pipeline, then calls onSaved', async () => {
        const createBody = rs.fn();
        const pipelineBody = rs.fn();
        server.use(
            http.post('/api/sinks', async ({ request }) => {
                createBody(await request.json());

                return HttpResponse.json(createdSink);
            }),
            http.patch('/api/projects/{project_id}/pipeline', async ({ request }) => {
                pipelineBody(await request.json());

                return HttpResponse.json(getMockedPipeline());
            })
        );
        const onSaved = rs.fn();
        const user = userEvent.setup();

        render(<AddMqttSink onSaved={onSaved} />);

        expect(screen.getByRole('textbox', { name: 'Name' })).toHaveValue('MQTT sink');
        await fillForm(user);
        const port = screen.getByRole('textbox', { name: 'Broker Port' });
        await user.clear(port);
        await user.type(port, '8883');
        await user.tab();
        await user.click(screen.getByRole('button', { name: 'Add & Use' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
        expect(createBody).toHaveBeenCalledWith({
            name: 'My broker',
            sink_type: 'mqtt',
            broker_host: 'localhost',
            broker_port: 8883,
            topic: 'predictions',
            auth_required: true,
            rate_limit: null,
            output_formats: ['predictions'],
        });
        expect(pipelineBody).toHaveBeenCalledWith({ sink_id: 'new-sink-id' });
    });

    it('does not submit without a broker host', async () => {
        const createBody = rs.fn();
        server.use(
            http.post('/api/sinks', async ({ request }) => {
                createBody(await request.json());

                return HttpResponse.json(createdSink);
            })
        );
        const onSaved = rs.fn();
        const user = userEvent.setup();

        render(<AddMqttSink onSaved={onSaved} />);

        await user.click(screen.getByRole('checkbox', { name: 'Predictions' }));

        expect(screen.getByRole('textbox', { name: /Broker Host/i })).toHaveValue('');
        expect(screen.getByRole('button', { name: 'Add & Use' })).toBeDisabled();

        await user.click(screen.getByRole('button', { name: 'Add & Use' }));

        expect(createBody).not.toHaveBeenCalled();
        expect(onSaved).not.toHaveBeenCalled();
    });

    it('keeps every entered value and does not connect when saving fails', async () => {
        const pipelineBody = rs.fn();
        server.use(
            http.post('/api/sinks', () =>
                HttpResponse.json({ detail: 'Broker unreachable' } as never, { status: 400 })
            ),
            http.patch('/api/projects/{project_id}/pipeline', async ({ request }) => {
                pipelineBody(await request.json());

                return HttpResponse.json(getMockedPipeline());
            })
        );
        const onSaved = rs.fn();
        const user = userEvent.setup();

        render(<AddMqttSink onSaved={onSaved} />);

        await fillForm(user);
        await user.click(screen.getByRole('button', { name: 'Add & Use' }));

        expect(await screen.findByText(/Broker unreachable/)).toBeVisible();
        expect(screen.getByRole('textbox', { name: 'Name' })).toHaveValue('My broker');
        expect(screen.getByRole('textbox', { name: /Broker Host/i })).toHaveValue('localhost');
        expect(screen.getByRole('textbox', { name: 'Topic' })).toHaveValue('predictions');
        expect(screen.getByRole('switch', { name: 'Require Authentication' })).toBeChecked();
        expect(screen.getByRole('checkbox', { name: 'Predictions' })).toBeChecked();
        expect(pipelineBody).not.toHaveBeenCalled();
        expect(onSaved).not.toHaveBeenCalled();
    });
});
