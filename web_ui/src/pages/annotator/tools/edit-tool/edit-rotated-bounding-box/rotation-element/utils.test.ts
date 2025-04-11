// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { SideAnchorLocationsProps } from '../location';
import { Direction, getDirection } from './utils';

describe('rotation-elemet utils', () => {
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
