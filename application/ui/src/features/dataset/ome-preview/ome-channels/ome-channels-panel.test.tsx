// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { OmeChannelDisplaySetting, OmeImageInfo } from '@/api/types';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../../api/utils';
import { server } from '../../../../msw-node-setup';
import { OmeChannelsPanel } from './ome-channels-panel.component';

const info: OmeImageInfo = {
    container_format: 'ome_tiff',
    size_x: 64,
    size_y: 32,
    size_z: 1,
    size_c: 2,
    size_t: 1,
    dimension_order: 'XYZCT',
    pixel_type: 'uint8',
    significant_bits: null,
    is_big_tiff: false,
    channels: [{ index: 0, name: 'DAPI' }, { index: 1 }],
    pyramid_levels: [],
};

const settings: OmeChannelDisplaySetting[] = [
    { channel: 0, target: 'blue', enabled: true, window_min: 10, window_max: 200 },
    { channel: 1, target: 'green', enabled: false, window_min: 0, window_max: 255 },
];

describe('OmeChannelsPanel', () => {
    it('lists every channel and saves the edited display settings', async () => {
        const savedBodies: unknown[] = [];

        server.use(
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/channel-view', () =>
                HttpResponse.json({ settings, is_default: true })
            ),
            http.put('/api/projects/{project_id}/dataset/media/{media_id}/channel-view', async ({ request }) => {
                const body = await request.json();
                savedBodies.push(body);

                return HttpResponse.json({ ...body, is_default: false });
            })
        );

        render(<OmeChannelsPanel mediaId={'ome-1'} info={info} />);

        const dapi = await screen.findByRole('switch', { name: 'DAPI' });
        const unnamedChannel = screen.getByRole('switch', { name: 'Channel 1' });

        expect(dapi).toBeChecked();
        expect(unnamedChannel).not.toBeChecked();
        expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();

        await userEvent.click(unnamedChannel);
        await userEvent.click(screen.getByRole('button', { name: 'Save' }));

        await waitFor(() => expect(savedBodies).toHaveLength(1));
        expect(savedBodies[0]).toEqual({
            settings: [settings[0], { ...settings[1], enabled: true }],
        });
    });

    it('prevents saving two enabled channels on the same color', async () => {
        server.use(
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/channel-view', () =>
                HttpResponse.json({
                    settings: [settings[0], { ...settings[1], target: 'blue' }],
                    is_default: false,
                })
            )
        );

        render(<OmeChannelsPanel mediaId={'ome-1'} info={info} />);

        await userEvent.click(await screen.findByRole('switch', { name: 'Channel 1' }));

        expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
    });
});
