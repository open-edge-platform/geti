// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { getMockedTreeLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { DISTINCT_COLORS } from '../../../../create-project/components/distinct-colors';
import { getAvailableColors } from './utils';

describe('getAvailableColors', () => {
    it('no labels - all distinct colors are available', () => {
        const availableColors = getAvailableColors([]);

        expect(availableColors).toStrictEqual(DISTINCT_COLORS);
    });

    it('second color is taken - rest should be available', () => {
        const allColors = DISTINCT_COLORS;
        const takenColor = allColors.splice(1, 1)[0];

        expect(getAvailableColors([getMockedTreeLabel({ color: takenColor })])).toStrictEqual(allColors);
    });

    it('all of the colors taken - all of them should be available again', () => {
        const labels = DISTINCT_COLORS.map((color) => getMockedTreeLabel({ color }));

        expect(getAvailableColors(labels)).toStrictEqual(DISTINCT_COLORS);
    });

    it('more than all of the colors taken - rest should be available', () => {
        const labels = DISTINCT_COLORS.map((color) => getMockedTreeLabel({ color }));

        const allColors = DISTINCT_COLORS;
        const takenColor = allColors.splice(1, 1)[0];
        labels.push(getMockedTreeLabel({ color: takenColor }));

        expect(getAvailableColors(labels)).toStrictEqual(allColors);
    });

    it('more than two times all of the colors taken - rest should be available', () => {
        const labels = DISTINCT_COLORS.map((color) => getMockedTreeLabel({ color }));
        labels.concat(DISTINCT_COLORS.map((color) => getMockedTreeLabel({ color })));

        const allColors = DISTINCT_COLORS;
        const takenColor = allColors.splice(1, 1)[0];
        labels.push(getMockedTreeLabel({ color: takenColor }));

        expect(getAvailableColors(labels)).toStrictEqual(allColors);
    });
});
