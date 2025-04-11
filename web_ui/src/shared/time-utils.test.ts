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
