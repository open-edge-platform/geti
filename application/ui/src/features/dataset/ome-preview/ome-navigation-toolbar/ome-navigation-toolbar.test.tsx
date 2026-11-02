// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { OmeImageInfo } from '@/api/types';
import { fireEvent, screen } from '@testing-library/react';
import { getMockedOmePlane } from 'mocks/mock-media';
import { render } from 'test-utils/render';

import { OmeNavigationToolbar } from './ome-navigation-toolbar.component';

const info: OmeImageInfo = {
    container_format: 'ome_tiff',
    size_x: 64,
    size_y: 32,
    size_z: 5,
    size_c: 2,
    size_t: 3,
    dimension_order: 'XYZCT',
    pixel_type: 'uint16',
    significant_bits: null,
    is_big_tiff: false,
    channels: [{ index: 0, name: 'DAPI' }, { index: 1 }],
    pyramid_levels: [],
};

const plane = getMockedOmePlane({ z_index: 2, t_index: 1, size_z: 5, size_t: 3 });

const annotatedPlanes = [
    { media_id: 'a', z_index: 2, t_index: 1 },
    { media_id: 'b', z_index: 4, t_index: 1 },
    { media_id: 'c', z_index: 2, t_index: 0 },
];

describe('OmeNavigationToolbar', () => {
    it('shows the current plane and the number of annotated planes', () => {
        render(
            <OmeNavigationToolbar info={info} plane={plane} annotatedPlanes={annotatedPlanes} onSelectPlane={rs.fn()} />
        );

        expect(screen.getByRole('slider', { name: 'Z slice' })).toHaveValue('2');
        expect(screen.getByRole('slider', { name: 'Time point' })).toHaveValue('1');
        expect(screen.getByText('3 / 5')).toBeVisible();
        expect(screen.getByText('2 / 3')).toBeVisible();
        expect(screen.getByText('Annotated planes: 3')).toBeVisible();
    });

    it('selects another plane along each axis', () => {
        const onSelectPlane = rs.fn();

        render(
            <OmeNavigationToolbar
                info={info}
                plane={plane}
                annotatedPlanes={annotatedPlanes}
                onSelectPlane={onSelectPlane}
            />
        );

        fireEvent.keyDown(screen.getByRole('slider', { name: 'Z slice' }), { key: 'ArrowRight' });
        fireEvent.keyUp(screen.getByRole('slider', { name: 'Z slice' }), { key: 'ArrowRight' });
        expect(onSelectPlane).toHaveBeenLastCalledWith(3, 1);

        fireEvent.keyDown(screen.getByRole('slider', { name: 'Time point' }), { key: 'ArrowLeft' });
        fireEvent.keyUp(screen.getByRole('slider', { name: 'Time point' }), { key: 'ArrowLeft' });
        expect(onSelectPlane).toHaveBeenLastCalledWith(2, 0);
    });

    it('disables the axes an image does not have', () => {
        render(
            <OmeNavigationToolbar
                info={{ ...info, size_t: 1 }}
                plane={{ ...plane, t_index: 0 }}
                annotatedPlanes={[]}
                onSelectPlane={rs.fn()}
            />
        );

        expect(screen.getByRole('slider', { name: 'Time point' })).toBeDisabled();
        expect(screen.getByRole('slider', { name: 'Z slice' })).toBeEnabled();
    });
});
