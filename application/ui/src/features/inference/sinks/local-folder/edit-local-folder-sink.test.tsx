// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { LocalFolderSinkConfig } from '@/api/types';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { EditLocalFolderSink } from './edit-local-folder-sink.component';

const sink: LocalFolderSinkConfig = {
    id: 'existing-sink-id',
    name: 'Folder sink',
    sink_type: 'folder',
    rate_limit: null,
    folder_path: '/data/old',
    output_formats: ['predictions'],
};

const setupHandlers = () => {
    const updateSink = rs.fn();
    const connectSink = rs.fn();

    server.use(
        http.patch('/api/sinks/{sink_id}', async ({ request }) => {
            updateSink(await request.json());

            return HttpResponse.json(sink);
        }),
        http.patch('/api/projects/{project_id}/pipeline', async ({ request }) => {
            connectSink(await request.json());

            return HttpResponse.json({} as never);
        }),
        http.post('/api/sinks/{sink_id}:test', () => HttpResponse.json({ reachable: true }))
    );

    return { updateSink, connectSink };
};

const renderEdit = ({ isConnected = false, onSaved = rs.fn(), editedSink = sink } = {}) =>
    render(
        <EditLocalFolderSink sink={editedSink} isConnected={isConnected} onSaved={onSaved} onBackToList={rs.fn()} />
    );

const changeFolderPath = async (path: string) => {
    const input = screen.getByRole('textbox', { name: /Folder Path/i });

    await userEvent.clear(input);
    await userEvent.type(input, path);
};

describe('EditLocalFolderSink', () => {
    it('prefills the form from the sink', () => {
        renderEdit();

        expect(screen.getByRole('textbox', { name: 'Name' })).toHaveValue('Folder sink');
        expect(screen.getByRole('textbox', { name: /Folder Path/i })).toHaveValue('/data/old');
        expect(screen.getByRole('checkbox', { name: 'Predictions' })).toBeChecked();
    });

    it('saves without id and sink_type in the body and does not connect on "Save"', async () => {
        const onSaved = rs.fn();
        const { updateSink, connectSink } = setupHandlers();

        renderEdit({ onSaved });

        await changeFolderPath('/data/new');
        await userEvent.click(screen.getByRole('button', { name: 'Save' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
        expect(connectSink).not.toHaveBeenCalled();
        expect(updateSink).toHaveBeenCalledTimes(1);
        expect(updateSink).toHaveBeenCalledWith({
            name: 'Folder sink',
            folder_path: '/data/new',
            rate_limit: null,
            output_formats: ['predictions'],
        });
    });

    it('prefills the rate limit and output formats, and patches the changed ones', async () => {
        const onSaved = rs.fn();
        const { updateSink } = setupHandlers();

        renderEdit({
            onSaved,
            editedSink: { ...sink, rate_limit: 0.2, output_formats: ['predictions', 'image_original'] },
        });

        expect(screen.getByRole('textbox', { name: /Samples/i })).toHaveValue('0.2');
        expect(screen.getByRole('textbox', { name: /Seconds/i })).toHaveValue('1');
        expect(screen.getByRole('checkbox', { name: 'Predictions' })).toBeChecked();
        expect(screen.getByRole('checkbox', { name: 'Image Original' })).toBeChecked();
        expect(screen.getByRole('checkbox', { name: 'Image with Predictions' })).not.toBeChecked();

        const samples = screen.getByRole('textbox', { name: /Samples/i });
        const seconds = screen.getByRole('textbox', { name: /Seconds/i });
        await userEvent.clear(samples);
        await userEvent.type(samples, '3');
        await userEvent.clear(seconds);
        await userEvent.type(seconds, '1');
        await userEvent.click(screen.getByRole('checkbox', { name: 'Image Original' }));
        await userEvent.click(screen.getByRole('checkbox', { name: 'Image with Predictions' }));
        await userEvent.click(screen.getByRole('button', { name: 'Save' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
        expect(updateSink).toHaveBeenCalledTimes(1);
        expect(updateSink).toHaveBeenCalledWith({
            name: 'Folder sink',
            folder_path: '/data/old',
            rate_limit: 3,
            output_formats: ['predictions', 'image_with_predictions'],
        });
    });

    it('connects the sink to the pipeline after "Save & Connect"', async () => {
        const onSaved = rs.fn();
        const { updateSink, connectSink } = setupHandlers();

        renderEdit({ onSaved });

        await changeFolderPath('/data/new');
        await userEvent.click(screen.getByRole('button', { name: 'Save & Connect' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
        expect(updateSink).toHaveBeenCalledTimes(1);
        expect(connectSink).toHaveBeenCalledWith({ sink_id: sink.id });
    });

    it('hides "Save & Connect" when the sink is already connected', () => {
        renderEdit({ isConnected: true });

        expect(screen.getByRole('button', { name: 'Save' })).toBeVisible();
        expect(screen.queryByRole('button', { name: 'Save & Connect' })).not.toBeInTheDocument();
    });

    it('keeps the entered values and does not call onSaved when saving fails', async () => {
        const onSaved = rs.fn();
        const { connectSink } = setupHandlers();
        server.use(
            http.patch('/api/sinks/{sink_id}', () =>
                HttpResponse.json({ detail: 'Folder is not writable' } as never, { status: 400 })
            )
        );

        renderEdit({ onSaved });

        await changeFolderPath('/root');
        await userEvent.click(screen.getByRole('checkbox', { name: 'Image Original' }));
        await userEvent.click(screen.getByRole('button', { name: 'Save' }));

        expect(await screen.findByLabelText('toast')).toHaveTextContent(
            'Failed to save sink configuration, Folder is not writable'
        );
        expect(screen.getByText('Edit sink')).toBeVisible();
        expect(screen.getByRole('textbox', { name: /Folder Path/i })).toHaveValue('/root');
        expect(screen.getByRole('checkbox', { name: 'Predictions' })).toBeChecked();
        expect(screen.getByRole('checkbox', { name: 'Image Original' })).toBeChecked();
        expect(connectSink).not.toHaveBeenCalled();
        expect(onSaved).not.toHaveBeenCalled();
    });
});
