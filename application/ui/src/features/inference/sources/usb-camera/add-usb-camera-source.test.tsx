// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { AddUsbCameraSource } from './add-usb-camera-source.component';

const devices = [
    { index: 0, name: 'Integrated Webcam' },
    { index: 1, name: 'Logitech C920' },
];

const setup = (cameras = devices) => {
    const createSpy = rs.fn();
    const pipelineSpy = rs.fn();
    const onSaved = rs.fn();

    server.use(
        http.get('/api/system/devices/camera', () => HttpResponse.json(cameras)),
        http.post('/api/sources/{source_id}:test', () => HttpResponse.json({ reachable: true })),
        http.patch('/api/projects/{project_id}/pipeline', async ({ request }) => {
            pipelineSpy(await request.json());

            return HttpResponse.json({ project_id: '123', status: 'idle', device: 'cpu' });
        })
    );

    render(<AddUsbCameraSource existingNames={[]} onSaved={onSaved} />);

    return { createSpy, pipelineSpy, onSaved };
};

const selectCamera = async (name: string) => {
    await userEvent.click(await screen.findByRole('button', { name: /Camera list/i }));
    await userEvent.click(await screen.findByRole('option', { name }));
};

describe('AddUsbCameraSource', () => {
    it('creates the source without id, connects it and calls onSaved', async () => {
        const createSpy = rs.fn();
        server.use(
            http.post('/api/sources', async ({ request }) => {
                const body = await request.json();
                createSpy(body);

                return HttpResponse.json({ ...(body as object), id: 'new-id' } as never);
            })
        );
        const { pipelineSpy, onSaved } = setup();

        await selectCamera('Logitech C920');
        await userEvent.click(screen.getByRole('button', { name: 'Add & Use' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
        expect(createSpy).toHaveBeenCalledWith({ name: 'USB camera source', source_type: 'usb_camera', device_id: 1 });
        expect(pipelineSpy).toHaveBeenCalledWith({ source_id: 'new-id' });
    });

    it('disables "Add & Use" and creates no source while no camera is selected', async () => {
        const createSpy = rs.fn();
        server.use(
            http.post('/api/sources', () => {
                createSpy();

                return HttpResponse.json({} as never);
            })
        );
        const { onSaved } = setup([]);

        const addButton = await screen.findByRole('button', { name: 'Add & Use' });
        expect(addButton).toBeDisabled();

        await userEvent.click(addButton);

        expect(createSpy).not.toHaveBeenCalled();
        expect(onSaved).not.toHaveBeenCalled();
    });

    it('lists a camera attached after refreshing the camera list and creates the source with it', async () => {
        const createSpy = rs.fn();
        server.use(
            http.post('/api/sources', async ({ request }) => {
                const body = await request.json();
                createSpy(body);

                return HttpResponse.json({ ...(body as object), id: 'new-id' } as never);
            })
        );
        const { onSaved } = setup([devices[0]]);
        const getOptionNames = () => screen.getAllByRole('option').map((option) => option.textContent);

        await userEvent.click(await screen.findByRole('button', { name: /Camera list/i }));
        await waitFor(() => expect(getOptionNames()).toEqual(['Integrated Webcam']));
        await userEvent.keyboard('{Escape}');

        server.use(http.get('/api/system/devices/camera', () => HttpResponse.json(devices)));
        await userEvent.click(screen.getByRole('button', { name: 'Refresh Cameras' }));

        await userEvent.click(screen.getByRole('button', { name: /Camera list/i }));
        await waitFor(() => expect(getOptionNames()).toEqual(['Integrated Webcam', 'Logitech C920']));
        await userEvent.click(screen.getByRole('option', { name: 'Logitech C920' }));
        await userEvent.click(screen.getByRole('button', { name: 'Add & Use' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
        expect(createSpy).toHaveBeenCalledWith({ name: 'USB camera source', source_type: 'usb_camera', device_id: 1 });
    });

    it('keeps the entered values when saving fails', async () => {
        server.use(http.post('/api/sources', () => HttpResponse.json({ detail: 'boom' } as never, { status: 500 })));
        const { pipelineSpy, onSaved } = setup();

        await userEvent.clear(await screen.findByRole('textbox', { name: /Name/i }));
        await userEvent.type(screen.getByRole('textbox', { name: /Name/i }), 'Door camera');
        await selectCamera('Logitech C920');
        await userEvent.click(screen.getByRole('button', { name: 'Add & Use' }));

        expect(await screen.findByText(/Failed to save source configuration/)).toBeVisible();
        expect(screen.getByRole('textbox', { name: /Name/i })).toHaveValue('Door camera');
        expect(screen.getByRole('button', { name: /Camera list/i })).toHaveTextContent('Logitech C920');
        expect(pipelineSpy).not.toHaveBeenCalled();
        expect(onSaved).not.toHaveBeenCalled();
    });
});
