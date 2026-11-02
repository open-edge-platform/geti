// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { OmeChannelDisplaySetting } from '@/api/types';

import { getDeclaredValueRange, getRenderLevel, getRenderVersion } from './ome-render.utils';

const level = (index: number, width: number, height: number) => ({ level: index, width, height, scale: [1, 1] });

const setting: OmeChannelDisplaySetting = { channel: 0, target: 'red', enabled: true, window_min: 0, window_max: 100 };

describe('ome-render utils', () => {
    describe('getRenderLevel', () => {
        it('renders the full resolution of non-pyramidal images', () => {
            expect(getRenderLevel({ pyramid_levels: [] })).toBe(0);
        });

        it('picks the most detailed level that fits', () => {
            const info = { pyramid_levels: [level(0, 40000, 30000), level(1, 10000, 7500), level(2, 2500, 1875)] };

            expect(getRenderLevel(info, 8192)).toBe(2);
            expect(getRenderLevel(info, 10000)).toBe(1);
            expect(getRenderLevel(info, 50000)).toBe(0);
        });

        it('falls back to the least detailed level when none fits', () => {
            expect(getRenderLevel({ pyramid_levels: [level(0, 40000, 30000), level(1, 20000, 15000)] }, 8192)).toBe(1);
        });
    });

    describe('getRenderVersion', () => {
        it('is stable for identical settings and changes with them', () => {
            expect(getRenderVersion([setting])).toBe(getRenderVersion([{ ...setting }]));
            expect(getRenderVersion([setting])).not.toBe(getRenderVersion([{ ...setting, window_max: 101 }]));
            expect(getRenderVersion([setting])).not.toBe(getRenderVersion([{ ...setting, enabled: false }]));
        });
    });

    describe('getDeclaredValueRange', () => {
        it.each([
            [
                { pixel_type: 'uint8', significant_bits: null },
                { min: 0, max: 255 },
            ],
            [
                { pixel_type: 'uint16', significant_bits: null },
                { min: 0, max: 65535 },
            ],
            [
                { pixel_type: 'uint16', significant_bits: 12 },
                { min: 0, max: 4095 },
            ],
        ])('derives the range of %o', (info, expected) => {
            expect(getDeclaredValueRange(info, [])).toEqual(expected);
        });

        it('allows headroom around the windows of float images', () => {
            const floatSetting = { ...setting, window_min: -1, window_max: 3 };

            expect(getDeclaredValueRange({ pixel_type: 'float', significant_bits: null }, [floatSetting])).toEqual({
                min: -1,
                max: 6,
            });
        });
    });
});
