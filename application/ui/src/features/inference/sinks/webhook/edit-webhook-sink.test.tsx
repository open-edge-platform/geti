// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { WebhookSinkConfig } from '@/api/types';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { EditWebhookSink } from './edit-webhook-sink.component';

const sink: WebhookSinkConfig = {
    id: 'sink-1',
    name: 'My webhook',
    sink_type: 'webhook',
    webhook_url: 'https://hooks.local/geti',
    http_method: 'PUT',
    timeout: 5,
    headers: { 'X-Key': 'first', 'X-Other': 'second' },
    rate_limit: null,
    output_formats: ['predictions'],
};

const setupHandlers = () => {
    const updateSink = rs.fn();
    const connectSink = rs.fn();

    server.use(
        http.patch('/api/sinks/{sink_id}', async ({ request }) => {
            const body = await request.json();
            updateSink(body);

            return HttpResponse.json({ ...sink, ...(body as object) } as never);
        }),
        http.post('/api/sinks/{sink_id}:test', () => HttpResponse.json({ reachable: true })),
        http.get('/api/sinks/{sink_id}', () => HttpResponse.json(sink)),
        http.patch('/api/projects/{project_id}/pipeline', async ({ request }) => {
            connectSink(await request.json());

            return HttpResponse.json({} as never);
        })
    );

    return { updateSink, connectSink };
};

const renderEdit = (isConnected = false, editedSink: WebhookSinkConfig = sink) => {
    const onSaved = rs.fn();

    render(<EditWebhookSink sink={editedSink} isConnected={isConnected} onSaved={onSaved} onBackToList={rs.fn()} />);

    return { onSaved };
};

const getInputValues = (name: string) =>
    screen.getAllByRole('textbox', { name }).map((input) => (input as HTMLInputElement).value);

describe('EditWebhookSink', () => {
    it('shows the saved values with existing headers as rows', () => {
        renderEdit();

        expect(screen.getByRole('textbox', { name: 'Name' })).toHaveValue('My webhook');
        expect(screen.getByRole('textbox', { name: /Webhook URL/ })).toHaveValue('https://hooks.local/geti');
        expect(getInputValues('headers-keys')).toEqual(['X-Key', 'X-Other']);
        expect(getInputValues('headers-values')).toEqual(['first', 'second']);
    });

    it('saves without connecting; removed rows leave the body; body has no id and sink_type', async () => {
        const { updateSink, connectSink } = setupHandlers();
        const { onSaved } = renderEdit();

        await userEvent.click(screen.getAllByRole('button', { name: 'Remove' })[0]);
        await userEvent.click(screen.getByRole('button', { name: 'Save' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));

        const body = updateSink.mock.calls[0][0];
        expect(body).toEqual({
            name: 'My webhook',
            webhook_url: 'https://hooks.local/geti',
            http_method: 'PUT',
            timeout: 5,
            headers: { 'X-Other': 'second' },
            rate_limit: null,
            output_formats: ['predictions'],
        });
        expect(body).not.toHaveProperty('id');
        expect(body).not.toHaveProperty('sink_type');
        expect(connectSink).not.toHaveBeenCalled();
    });

    it('patches a changed webhook URL', async () => {
        const { updateSink } = setupHandlers();
        const { onSaved } = renderEdit();

        const url = screen.getByRole('textbox', { name: /Webhook URL/ });
        await userEvent.clear(url);
        await userEvent.type(url, 'https://hooks.local/v2');
        await userEvent.click(screen.getByRole('button', { name: 'Save' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
        expect(updateSink).toHaveBeenCalledWith({
            name: 'My webhook',
            webhook_url: 'https://hooks.local/v2',
            http_method: 'PUT',
            timeout: 5,
            headers: { 'X-Key': 'first', 'X-Other': 'second' },
            rate_limit: null,
            output_formats: ['predictions'],
        });
    });

    it('patches a changed HTTP method and a header added next to the existing ones', async () => {
        const { updateSink } = setupHandlers();
        const { onSaved } = renderEdit();

        await userEvent.click(screen.getByRole('button', { name: /HTTP Method/ }));
        await userEvent.click(screen.getByRole('option', { name: 'PATCH' }));
        await userEvent.click(screen.getByRole('button', { name: 'Add header' }));
        await userEvent.type(screen.getAllByRole('textbox', { name: 'headers-keys' })[2], 'X-Trace');
        await userEvent.type(screen.getAllByRole('textbox', { name: 'headers-values' })[2], 'on');
        await userEvent.click(screen.getByRole('button', { name: 'Save' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
        expect(updateSink).toHaveBeenCalledWith({
            name: 'My webhook',
            webhook_url: 'https://hooks.local/geti',
            http_method: 'PATCH',
            timeout: 5,
            headers: { 'X-Key': 'first', 'X-Other': 'second', 'X-Trace': 'on' },
            rate_limit: null,
            output_formats: ['predictions'],
        });
    });

    it('patches empty headers after the only header is removed', async () => {
        const { updateSink } = setupHandlers();
        const { onSaved } = renderEdit(false, { ...sink, headers: { Authorization: 'Bearer token' } });

        await userEvent.click(screen.getByRole('button', { name: 'Remove' }));
        await userEvent.click(screen.getByRole('button', { name: 'Save' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
        expect(updateSink).toHaveBeenCalledWith({
            name: 'My webhook',
            webhook_url: 'https://hooks.local/geti',
            http_method: 'PUT',
            timeout: 5,
            headers: {},
            rate_limit: null,
            output_formats: ['predictions'],
        });
    });

    it('connects to the pipeline on "Save & Connect"', async () => {
        const { updateSink, connectSink } = setupHandlers();
        const { onSaved } = renderEdit();

        await userEvent.type(screen.getByRole('textbox', { name: 'Name' }), '!');
        await userEvent.click(screen.getByRole('button', { name: 'Save & Connect' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));

        expect(updateSink).toHaveBeenCalledTimes(1);
        expect(connectSink).toHaveBeenCalledWith({ sink_id: 'sink-1' });
    });

    it('disables the buttons until the state is changed', async () => {
        renderEdit();

        expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
        expect(screen.getByRole('button', { name: 'Save & Connect' })).toBeDisabled();

        await userEvent.type(screen.getByRole('textbox', { name: 'Name' }), '!');

        expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled();
    });

    it('hides "Save & Connect" when the sink is already connected', () => {
        renderEdit(true);

        expect(screen.queryByRole('button', { name: 'Save & Connect' })).not.toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Save' })).toBeVisible();
    });

    it('rejects duplicate header keys and sends no request', async () => {
        const { updateSink } = setupHandlers();
        const { onSaved } = renderEdit();

        const keys = screen.getAllByRole('textbox', { name: 'headers-keys' });
        await userEvent.clear(keys[1]);
        await userEvent.type(keys[1], 'X-Key');

        expect(screen.getAllByRole('textbox', { name: 'headers-keys' })[1]).toHaveAttribute('aria-invalid', 'true');
        expect(screen.getByText('Key must be unique')).toBeVisible();

        expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
        await userEvent.click(screen.getByRole('button', { name: 'Save' }));

        expect(updateSink).not.toHaveBeenCalled();
        expect(onSaved).not.toHaveBeenCalled();
    });

    it('keeps every row and field after a failed save', async () => {
        const { connectSink } = setupHandlers();
        server.use(
            http.patch('/api/sinks/{sink_id}', () => HttpResponse.json({ detail: 'Boom' } as never, { status: 500 }))
        );
        const { onSaved } = renderEdit();

        await userEvent.clear(screen.getByRole('textbox', { name: 'Name' }));
        await userEvent.type(screen.getByRole('textbox', { name: 'Name' }), 'Renamed');
        await userEvent.click(screen.getByRole('button', { name: 'Add header' }));
        await userEvent.type(screen.getAllByRole('textbox', { name: 'headers-keys' })[2], 'X-New');
        await userEvent.type(screen.getAllByRole('textbox', { name: 'headers-values' })[2], 'third');
        await userEvent.click(screen.getByRole('button', { name: 'Save & Connect' }));

        expect(await screen.findByLabelText('toast')).toHaveTextContent('Boom');

        expect(screen.getByRole('textbox', { name: 'Name' })).toHaveValue('Renamed');
        expect(getInputValues('headers-keys')).toEqual(['X-Key', 'X-Other', 'X-New']);
        expect(getInputValues('headers-values')).toEqual(['first', 'second', 'third']);
        expect(connectSink).not.toHaveBeenCalled();
        expect(onSaved).not.toHaveBeenCalled();
    });
});
