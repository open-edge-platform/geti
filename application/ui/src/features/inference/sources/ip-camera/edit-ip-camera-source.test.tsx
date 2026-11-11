// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { IPCameraSourceConfig } from '@/api/types';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { EditIpCameraSource } from './edit-ip-camera-source.component';

const source: IPCameraSourceConfig = {
    id: 'source-id',
    name: 'Gate camera',
    source_type: 'ip_camera',
    stream_url: 'rtsp://gate.local/stream',
    auth_required: false,
};

describe('EditIpCameraSource', () => {
    const onSaved = rs.fn();
    const pipelineSpy = rs.fn();
    const updateBody = rs.fn();

    beforeEach(() => {
        onSaved.mockClear();
        pipelineSpy.mockClear();
        updateBody.mockClear();
        server.use(
            http.patch('/api/sources/{source_id}', async ({ request }) => {
                updateBody(await request.json());

                return HttpResponse.json(source);
            }),
            http.post('/api/sources/{source_id}:test', () =>
                HttpResponse.json({ reachable: true, latency_ms: 10, error: null })
            ),
            http.patch('/api/projects/{project_id}/pipeline', async ({ request }) => {
                pipelineSpy(await request.json());

                return HttpResponse.json({} as never);
            })
        );
    });

    const renderEdit = (isConnected = false) =>
        render(
            <EditIpCameraSource source={source} isConnected={isConnected} onSaved={onSaved} onBackToList={rs.fn()} />
        );

    const editStreamUrl = async (user: ReturnType<typeof userEvent.setup>, url: string) => {
        const field = screen.getByRole('textbox', { name: /Stream Url/i });
        await user.clear(field);
        await user.type(field, url);
    };

    it('sends PATCH without id and source_type and does not connect on "Save"', async () => {
        const user = userEvent.setup();
        renderEdit();

        await editStreamUrl(user, 'rtsp://new/stream');
        await user.click(screen.getByRole('button', { name: 'Save' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
        expect(updateBody).toHaveBeenCalledWith({
            name: 'Gate camera',
            stream_url: 'rtsp://new/stream',
            auth_required: false,
        });
        expect(pipelineSpy).not.toHaveBeenCalled();
    });

    it('connects to the pipeline only on "Save & Connect"', async () => {
        const user = userEvent.setup();
        renderEdit();

        await editStreamUrl(user, 'rtsp://new/stream');
        await user.click(screen.getByRole('switch', { name: 'Require Authentication' }));
        await user.click(screen.getByRole('button', { name: /Save & Connect/i }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
        expect(updateBody).toHaveBeenCalledWith({
            name: 'Gate camera',
            stream_url: 'rtsp://new/stream',
            auth_required: true,
        });
        expect(pipelineSpy).toHaveBeenCalledWith({ source_id: 'source-id' });
    });

    it('disables "Save" and "Save & Connect" until a value changes', async () => {
        const user = userEvent.setup();
        renderEdit();

        expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
        expect(screen.getByRole('button', { name: /Save & Connect/i })).toBeDisabled();

        await editStreamUrl(user, 'rtsp://new/stream');

        expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled();
        expect(screen.getByRole('button', { name: /Save & Connect/i })).toBeEnabled();
    });

    it('hides "Save & Connect" when the source is connected', () => {
        renderEdit(true);

        expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /Save & Connect/i })).not.toBeInTheDocument();
    });

    it('keeps the edited values when updating fails', async () => {
        server.use(
            http.patch('/api/sources/{source_id}', () =>
                HttpResponse.json({ detail: 'boom' } as never, { status: 500 })
            )
        );
        const user = userEvent.setup();
        renderEdit();

        const nameField = screen.getByRole('textbox', { name: /Name/i });
        await user.clear(nameField);
        await user.type(nameField, 'Renamed');
        await editStreamUrl(user, 'not-a-url');
        await user.click(screen.getByRole('button', { name: /Save & Connect/i }));

        expect(await screen.findByText('Failed to save source configuration, boom')).toBeVisible();
        expect(screen.getByText('Edit input source')).toBeVisible();
        expect(screen.getByRole('textbox', { name: /Name/i })).toHaveValue('Renamed');
        expect(screen.getByRole('textbox', { name: /Stream Url/i })).toHaveValue('not-a-url');
        expect(pipelineSpy).not.toHaveBeenCalled();
        expect(onSaved).not.toHaveBeenCalled();
    });
});
