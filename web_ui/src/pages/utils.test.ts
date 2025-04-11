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

import { VALID_IMAGE_TYPES_SINGLE_UPLOAD } from '../shared/media-utils';
import { getForegroundColor, getPointInRoi, hexaToRGBA, isSupportedImageFormat } from './utils';

const mockedRoi = {
    x: 0,
    y: 0,
    width: 100,
    height: 100,
};

describe('page utils', () => {
    describe('isSupportedImageFormat', () => {
        it('valid file', () => {
            const validFile = new File(['foo'], 'foo.txt', {
                type: `img/${VALID_IMAGE_TYPES_SINGLE_UPLOAD[0]}`,
            });

            expect(isSupportedImageFormat(validFile)).toBe(true);
        });

        it('invalid file', () => {
            const invalidFile = new File(['foo'], 'foo.txt', {
                type: 'text/plain',
            });

            expect(isSupportedImageFormat(invalidFile)).toBe(false);
        });

        it('no type', () => {
            const invalidFile = new File(['foo'], 'foo.txt');
            expect(isSupportedImageFormat(invalidFile)).toBe(false);
        });
    });

    it('hexaToRGBA', () => {
        expect(hexaToRGBA('')).toEqual([0, 0, 0, 0]);
        expect(hexaToRGBA('#000')).toEqual([0, 0, 0, 1]);
        expect(hexaToRGBA('#fffff')).toEqual([255, 255, 255, 255]);
        expect(hexaToRGBA('#000000ff')).toEqual([0, 0, 0, 255]);
    });

    it('getForegroundColor', () => {
        const lowContrast = 'test-1';
        const highContrast = 'test-2';

        expect(getForegroundColor([0, 0, 0, 0], lowContrast, highContrast)).toBe(highContrast);
        expect(getForegroundColor([255, 255, 255, 255], lowContrast, highContrast)).toBe(lowContrast);
    });

    it('getPointInRoi', () => {
        const xUnderRoi = { x: mockedRoi.x - 10, y: mockedRoi.y };
        const xAboveRoi = { x: mockedRoi.width + 10, y: mockedRoi.y };
        const yUnderRoi = { x: mockedRoi.x, y: mockedRoi.y - 10 };
        const yAboveRoi = { x: mockedRoi.x, y: mockedRoi.height + 10 };

        expect(getPointInRoi(xUnderRoi, mockedRoi).x).toEqual(mockedRoi.x);
        expect(getPointInRoi(xAboveRoi, mockedRoi).x).toEqual(mockedRoi.width);

        expect(getPointInRoi(yUnderRoi, mockedRoi).y).toEqual(mockedRoi.y);
        expect(getPointInRoi(yAboveRoi, mockedRoi).y).toEqual(mockedRoi.height);
    });
});
