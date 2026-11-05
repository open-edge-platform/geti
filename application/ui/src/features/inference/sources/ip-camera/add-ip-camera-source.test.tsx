// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { AddIpCameraSource } from './add-ip-camera-source.component';

describe('AddIpCameraSource', () => {
    const onSaved = rs.fn();

    beforeEach(() => {
        onSaved.mockClear();
        server.use(
            http.post('/api/sources/{source_id}:test', () =>
                HttpResponse.json({ reachable: true, latency_ms: 10, error: null })
            )
        );
    });

    const fillAndSubmit = async (name: string, url: string) => {
        const user = userEvent.setup();
        const nameField = screen.getByRole('textbox', { name: /Name/i });
        await user.clear(nameField);
        await user.type(nameField, name);
        await user.type(screen.getByRole('textbox', { name: /Stream Url/i }), url);

        return user;
    };

    it('creates the source without id, connects it to the pipeline and calls onSaved', async () => {
        const createBody = rs.fn();
        const pipelineBody = rs.fn();
        server.use(
            http.post('/api/sources', async ({ request }) => {
                const body = await request.json();
                createBody(body);

                return HttpResponse.json({ ...body, id: 'new-id' });
            }),
            http.patch('/api/projects/{project_id}/pipeline', async ({ request }) => {
                pipelineBody(await request.json());

                return HttpResponse.json({} as never);
            })
        );

        render(<AddIpCameraSource existingNames={[]} onSaved={onSaved} />);
        const user = await fillAndSubmit('Door camera', 'rtsp://door/stream');
        await user.click(screen.getByRole('switch', { name: 'Require Authentication' }));
        await user.click(screen.getByRole('button', { name: /Add & Use/i }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
        expect(createBody).toHaveBeenCalledWith({
            name: 'Door camera',
            source_type: 'ip_camera',
            stream_url: 'rtsp://door/stream',
            auth_required: true,
        });
        expect(pipelineBody).toHaveBeenCalledWith({ source_id: 'new-id' });
    });

    it('disables "Add & Use" until the stream url is provided', async () => {
        const user = userEvent.setup();
        render(<AddIpCameraSource existingNames={[]} onSaved={rs.fn()} />);

        expect(screen.getByRole('button', { name: 'Add & Use' })).toBeDisabled();

        await user.type(screen.getByRole('textbox', { name: /Stream Url/i }), 'rtsp://door/stream');

        expect(screen.getByRole('button', { name: 'Add & Use' })).toBeEnabled();
    });

    it('keeps the typed values and does not connect when creating fails', async () => {
        const pipelineSpy = rs.fn();
        server.use(
            http.post('/api/sources', () => HttpResponse.json({ detail: 'boom' } as never, { status: 500 })),
            http.patch('/api/projects/{project_id}/pipeline', () => {
                pipelineSpy();

                return HttpResponse.json({} as never);
            })
        );

        render(<AddIpCameraSource existingNames={[]} onSaved={onSaved} />);
        const user = await fillAndSubmit('Door camera', 'not-a-url');
        await user.click(screen.getByRole('button', { name: /Add & Use/i }));

        expect(await screen.findByText(/boom/)).toBeVisible();
        expect(screen.getByRole('textbox', { name: /Name/i })).toHaveValue('Door camera');
        expect(screen.getByRole('textbox', { name: /Stream Url/i })).toHaveValue('not-a-url');
        expect(pipelineSpy).not.toHaveBeenCalled();
        expect(onSaved).not.toHaveBeenCalled();
    });
});
