// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { USBCameraSourceConfig } from '@/api/types';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { EditUsbCameraSource } from './edit-usb-camera-source.component';

const source: USBCameraSourceConfig = {
    id: 'usb-id',
    name: 'My USB',
    source_type: 'usb_camera',
    device_id: 0,
    codec: 'YUY2',
};

const setup = ({ isConnected = false, updateStatus = 200 } = {}) => {
    const updateSpy = rs.fn();
    const pipelineSpy = rs.fn();
    const onSaved = rs.fn();

    server.use(
        http.get('/api/system/devices/camera', () =>
            HttpResponse.json([
                { index: 0, name: 'Integrated Webcam' },
                { index: 1, name: 'Logitech C920' },
            ])
        ),
        http.patch('/api/sources/{source_id}', async ({ request }) => {
            updateSpy(await request.json());

            return updateStatus === 200
                ? HttpResponse.json(source)
                : HttpResponse.json({ detail: 'boom' } as never, { status: updateStatus as 500 });
        }),
        http.post('/api/sources/{source_id}:test', () => HttpResponse.json({ reachable: true })),
        http.patch('/api/projects/{project_id}/pipeline', async ({ request }) => {
            pipelineSpy(await request.json());

            return HttpResponse.json({ project_id: '123', status: 'idle', device: 'cpu' });
        })
    );

    render(<EditUsbCameraSource source={source} isConnected={isConnected} onSaved={onSaved} onBackToList={rs.fn()} />);

    return { updateSpy, pipelineSpy, onSaved };
};

describe('EditUsbCameraSource', () => {
    it('patches without id and source_type, keeps codec and does not connect on Save', async () => {
        const { updateSpy, pipelineSpy, onSaved } = setup();

        const name = await screen.findByRole('textbox', { name: /Name/i });
        await userEvent.clear(name);
        await userEvent.type(name, 'Renamed');
        await userEvent.click(screen.getByRole('button', { name: 'Save' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
        expect(updateSpy).toHaveBeenCalledWith({ name: 'Renamed', device_id: 0, codec: 'YUY2' });
        expect(pipelineSpy).not.toHaveBeenCalled();
    });

    it('connects the source to the pipeline after Save & Connect', async () => {
        const { updateSpy, pipelineSpy, onSaved } = setup();

        const name = await screen.findByRole('textbox', { name: /Name/i });
        await userEvent.clear(name);
        await userEvent.type(name, 'Renamed');
        await userEvent.click(screen.getByRole('button', { name: 'Save & Connect' }));

        await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
        expect(updateSpy).toHaveBeenCalledTimes(1);
        expect(pipelineSpy).toHaveBeenCalledWith({ source_id: 'usb-id' });
    });

    it('disables Save and Save & Connect until a value changes', async () => {
        setup();

        const name = await screen.findByRole('textbox', { name: /Name/i });
        expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
        expect(screen.getByRole('button', { name: 'Save & Connect' })).toBeDisabled();

        await userEvent.type(name, '!');

        expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled();
        expect(screen.getByRole('button', { name: 'Save & Connect' })).toBeEnabled();
    });

    it('hides Save & Connect when the source is connected', async () => {
        setup({ isConnected: true });

        expect(await screen.findByRole('button', { name: 'Save' })).toBeVisible();
        expect(screen.queryByRole('button', { name: 'Save & Connect' })).not.toBeInTheDocument();
    });

    it('keeps the edited values when saving fails', async () => {
        const { pipelineSpy, onSaved } = setup({ updateStatus: 500 });

        const name = await screen.findByRole('textbox', { name: /Name/i });
        await userEvent.clear(name);
        await userEvent.type(name, 'Door camera');
        await userEvent.click(screen.getByRole('button', { name: /Camera list/i }));
        await userEvent.click(await screen.findByRole('option', { name: 'Logitech C920' }));
        await userEvent.click(screen.getByRole('button', { name: 'Save & Connect' }));

        expect(await screen.findByText(/Failed to save source configuration/)).toBeVisible();
        expect(screen.getByRole('textbox', { name: /Name/i })).toHaveValue('Door camera');
        expect(screen.getByRole('button', { name: /Camera list/i })).toHaveTextContent('Logitech C920');
        expect(pipelineSpy).not.toHaveBeenCalled();
        expect(onSaved).not.toHaveBeenCalled();
    });
});
