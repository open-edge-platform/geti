// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { AddWebhookSink } from './add-webhook-sink.component';

const PIPELINE_PATH = '/api/projects/{project_id}/pipeline';

const setupHandlers = () => {
    const createSink = rs.fn();
    const connectSink = rs.fn();

    server.use(
        http.post('/api/sinks', async ({ request }) => {
            const body = await request.json();
            createSink(body);

            return HttpResponse.json({ ...(body as object), id: 'new-sink-id' } as never);
        }),
        http.post('/api/sinks/{sink_id}:test', () => HttpResponse.json({ reachable: true })),
        http.patch(PIPELINE_PATH, async ({ request }) => {
            connectSink(await request.json());

            return HttpResponse.json({} as never);
        })
    );

    return { createSink, connectSink };
};

const addHeader = async (key: string, value?: string) => {
    await userEvent.click(screen.getByRole('button', { name: 'Add header' }));

    const keys = screen.getAllByRole('textbox', { name: 'headers-keys' });
    await userEvent.type(keys[keys.length - 1], key);

    if (value !== undefined) {
        const values = screen.getAllByRole('textbox', { name: 'headers-values' });
        await userEvent.type(values[values.length - 1], value);
    }
};

const fillRequiredFields = async () => {
    await userEvent.type(screen.getByRole('textbox', { name: /Webhook URL/ }), 'https://hooks.local/geti');
    await userEvent.click(screen.getByRole('checkbox', { name: 'Predictions' }));
};

describe('AddWebhookSink', () => {
    it('creates the sink without an id, connects it to the pipeline and calls onSaved', async () => {
        const { createSink, connectSink } = setupHandlers();
        const onSaved = rs.fn();

        render(<AddWebhookSink onSaved={onSaved} />);

        expect(screen.getByRole('textbox', { name: 'Name' })).toHaveValue('Webhook sink');

        await fillRequiredFields();
        await addHeader('X-Key', 'first');
        await addHeader('Authorization', 'Bearer token');
        await userEvent.click(screen.getByRole('button', { name: 'Add & Use' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));

        expect(createSink).toHaveBeenCalledTimes(1);

        const body = createSink.mock.calls[0][0];
        expect(body).toEqual({
            name: 'Webhook sink',
            sink_type: 'webhook',
            webhook_url: 'https://hooks.local/geti',
            timeout: 10,
            http_method: 'POST',
            headers: { 'X-Key': 'first', Authorization: 'Bearer token' },
            rate_limit: null,
            output_formats: ['predictions'],
        });
        expect(body).not.toHaveProperty('id');
        expect(connectSink).toHaveBeenCalledWith({ sink_id: 'new-sink-id' });
    });

    it('rejects duplicate header keys and sends no request', async () => {
        const { createSink, connectSink } = setupHandlers();
        const onSaved = rs.fn();

        render(<AddWebhookSink onSaved={onSaved} />);

        await fillRequiredFields();
        await addHeader('X-Key', 'first');
        await addHeader('X-Key', 'second');

        const keys = screen.getAllByRole('textbox', { name: 'headers-keys' });

        expect(keys[0]).not.toHaveAttribute('aria-invalid', 'true');
        expect(keys[1]).toHaveAttribute('aria-invalid', 'true');
        expect(screen.getByText('Key must be unique')).toBeVisible();

        expect(screen.getByRole('button', { name: 'Add & Use' })).toBeDisabled();
        await userEvent.click(screen.getByRole('button', { name: 'Add & Use' }));

        expect(createSink).not.toHaveBeenCalled();
        expect(connectSink).not.toHaveBeenCalled();
        expect(onSaved).not.toHaveBeenCalled();
    });

    it('disables "Add & Use" until URL, an output format and every header row are provided', async () => {
        const { createSink } = setupHandlers();

        render(<AddWebhookSink onSaved={rs.fn()} />);

        const button = () => screen.getByRole('button', { name: 'Add & Use' });

        expect(button()).toBeDisabled();

        await fillRequiredFields();
        expect(button()).toBeEnabled();

        await userEvent.click(screen.getByRole('button', { name: 'Add header' }));
        expect(button()).toBeDisabled();

        await userEvent.type(screen.getByRole('textbox', { name: 'headers-keys' }), 'X-Key');
        expect(button()).toBeDisabled();

        await userEvent.type(screen.getByRole('textbox', { name: 'headers-values' }), 'v');
        expect(button()).toBeEnabled();
        expect(createSink).not.toHaveBeenCalled();
    });

    it('keeps every row and field after a failed save', async () => {
        const { connectSink } = setupHandlers();
        const onSaved = rs.fn();
        server.use(http.post('/api/sinks', () => HttpResponse.json({ detail: 'Boom' } as never, { status: 500 })));

        render(<AddWebhookSink onSaved={onSaved} />);

        await userEvent.clear(screen.getByRole('textbox', { name: 'Name' }));
        await userEvent.type(screen.getByRole('textbox', { name: 'Name' }), 'My hook');
        await fillRequiredFields();
        await addHeader('X-Key', 'first');
        await addHeader('X-Other', 'second');
        await userEvent.click(screen.getByRole('button', { name: 'Add & Use' }));

        expect(await screen.findByLabelText('toast')).toHaveTextContent('Boom');

        expect(screen.getByRole('textbox', { name: 'Name' })).toHaveValue('My hook');
        expect(screen.getByRole('textbox', { name: /Webhook URL/ })).toHaveValue('https://hooks.local/geti');
        expect(screen.getByRole('checkbox', { name: 'Predictions' })).toBeChecked();
        expect(
            screen.getAllByRole('textbox', { name: 'headers-keys' }).map((input) => (input as HTMLInputElement).value)
        ).toEqual(['X-Key', 'X-Other']);
        expect(
            screen.getAllByRole('textbox', { name: 'headers-values' }).map((input) => (input as HTMLInputElement).value)
        ).toEqual(['first', 'second']);
        expect(connectSink).not.toHaveBeenCalled();
        expect(onSaved).not.toHaveBeenCalled();
    });
});
