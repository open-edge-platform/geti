// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { SideAnchorLocationsProps } from '../location';
import { Direction, getDirection } from './utils';

describe('rotation-element utils', () => {
    describe('getDirection', () => {
        const rio = { x: 0, y: 0, width: 20, height: 20 };
        const offsidePoint = { x: rio.x - 1, y: rio.y - 1 };
        const insidePoint = { x: rio.x + 1, y: rio.y + 1 };
        const withGap = { N: offsidePoint, W: offsidePoint, S: offsidePoint, E: offsidePoint };

        it('N', () => {
            expect(getDirection({ withGap: { ...withGap, N: insidePoint } } as SideAnchorLocationsProps, rio)).toBe(
                Direction.N
            );
        });

        it('W', () => {
            expect(getDirection({ withGap: { ...withGap, W: insidePoint } } as SideAnchorLocationsProps, rio)).toBe(
                Direction.W
            );
        });

        it('S', () => {
            expect(getDirection({ withGap: { ...withGap, S: insidePoint } } as SideAnchorLocationsProps, rio)).toBe(
                Direction.S
            );
        });

        it('E', () => {
            expect(getDirection({ withGap: { ...withGap, E: insidePoint } } as SideAnchorLocationsProps, rio)).toBe(
                Direction.E
            );
        });

        it('MIDDLE', () => {
            expect(getDirection({ withGap } as SideAnchorLocationsProps, rio)).toBe(Direction.MIDDLE);
        });
    });
});
