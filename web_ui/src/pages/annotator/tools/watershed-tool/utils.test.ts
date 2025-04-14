// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
