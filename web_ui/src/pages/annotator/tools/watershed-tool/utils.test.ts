// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { getImageData } from '../../../../shared/canvas-utils';
import { getMaxSensitivityForImage } from './utils';

describe('utils', () => {
    describe('getMaxSensitivityForImage', () => {
        it('returns at least one sensitivity', () => {
            expect(getMaxSensitivityForImage(getImageData(new Image(0, 0)))).toEqual(1);
        });

        it('returns sensitivities available based on image', () => {
            expect(getMaxSensitivityForImage(getImageData(new Image(2000, 2000)))).toEqual(4);
        });

        it('uses the highest side of the image', () => {
            expect(getMaxSensitivityForImage(getImageData(new Image(2000, 0)))).toEqual(4);
            expect(getMaxSensitivityForImage(getImageData(new Image(0, 2000)))).toEqual(4);
        });

        it('very high image returns the last sensitivity', () => {
            expect(getMaxSensitivityForImage(getImageData(new Image(6000, 0)))).toEqual(5);
        });
    });
});
