// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { formatToHourMinSec, isFormattedHourMinSec } from './time-utils';

describe('time-utils', () => {
    it('isFormattedHourMinSec', () => {
        expect(isFormattedHourMinSec('01:00')).toBe(false);
        expect(isFormattedHourMinSec('01:00:00')).toBe(true);
    });

    it('formatToHourMinSec', () => {
        expect(formatToHourMinSec(1)).toBe('00:00:01');
        expect(formatToHourMinSec(120)).toBe('00:02:00');
        expect(formatToHourMinSec(3600)).toBe('01:00:00');
    });
});
