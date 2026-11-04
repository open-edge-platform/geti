// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { AddLocalFolderSink } from './add-local-folder-sink.component';

const NEW_SINK_ID = 'new-sink-id';

const setupHandlers = () => {
    const createSink = rs.fn();
    const connectSink = rs.fn();

    server.use(
        http.post('/api/sinks', async ({ request }) => {
            createSink(await request.json());

            return HttpResponse.json({
                id: NEW_SINK_ID,
                name: 'Folder sink',
                sink_type: 'folder',
                folder_path: '/data/out',
                output_formats: ['predictions'],
            });
        }),
        http.patch('/api/projects/{project_id}/pipeline', async ({ request }) => {
            connectSink(await request.json());

            return HttpResponse.json({} as never);
        }),
        http.post('/api/sinks/{sink_id}:test', () => HttpResponse.json({ reachable: true }))
    );

    return { createSink, connectSink };
};

const fillRequiredFields = async (folderPath: string) => {
    await userEvent.type(screen.getByRole('textbox', { name: /Folder Path/i }), folderPath);
    await userEvent.click(screen.getByRole('checkbox', { name: 'Predictions' }));
};

describe('AddLocalFolderSink', () => {
    it('creates the sink without id, connects it to the pipeline, then calls onSaved', async () => {
        const onSaved = rs.fn();
        const { createSink, connectSink } = setupHandlers();

        render(<AddLocalFolderSink onSaved={onSaved} />);

        await fillRequiredFields('/data/out');
        await userEvent.click(screen.getByRole('button', { name: 'Add & Use' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
        expect(createSink).toHaveBeenCalledTimes(1);
        expect(createSink).toHaveBeenCalledWith({
            name: 'Local folder sink',
            sink_type: 'folder',
            folder_path: '/data/out',
            rate_limit: null,
            output_formats: ['predictions'],
        });
        expect(connectSink).toHaveBeenCalledWith({ sink_id: NEW_SINK_ID });
    });

    it('sends the rate limit as samples per second when set', async () => {
        const { createSink } = setupHandlers();

        render(<AddLocalFolderSink onSaved={rs.fn()} />);

        await userEvent.type(screen.getByRole('textbox', { name: /Samples/i }), '4');
        await userEvent.type(screen.getByRole('textbox', { name: /Seconds/i }), '2');
        await fillRequiredFields('/data/out');
        await userEvent.click(screen.getByRole('button', { name: 'Add & Use' }));

        await waitFor(() => expect(createSink).toHaveBeenCalledWith(expect.objectContaining({ rate_limit: 2 })));
    });

    it('disables "Add & Use" until Folder Path and an output format are provided', async () => {
        render(<AddLocalFolderSink onSaved={rs.fn()} />);

        const button = () => screen.getByRole('button', { name: 'Add & Use' });

        expect(button()).toBeDisabled();

        await userEvent.click(screen.getByRole('checkbox', { name: 'Predictions' }));
        expect(button()).toBeDisabled();

        await userEvent.type(screen.getByRole('textbox', { name: /Folder Path/ }), '/data');
        expect(button()).toBeEnabled();

        await userEvent.click(screen.getByRole('checkbox', { name: 'Predictions' }));
        expect(button()).toBeDisabled();
    });

    it('keeps the entered values and does not connect when saving fails', async () => {
        const onSaved = rs.fn();
        const { connectSink } = setupHandlers();
        server.use(
            http.post('/api/sinks', () =>
                HttpResponse.json({ detail: 'Folder is not writable' } as never, { status: 400 })
            )
        );

        render(<AddLocalFolderSink onSaved={onSaved} />);

        await fillRequiredFields('/root');
        await userEvent.click(screen.getByRole('button', { name: 'Add & Use' }));

        expect(await screen.findByText(/Folder is not writable/)).toBeInTheDocument();
        expect(screen.getByRole('textbox', { name: /Folder Path/i })).toHaveValue('/root');
        expect(screen.getByRole('checkbox', { name: 'Predictions' })).toBeChecked();
        expect(connectSink).not.toHaveBeenCalled();
        expect(onSaved).not.toHaveBeenCalled();
    });
});
