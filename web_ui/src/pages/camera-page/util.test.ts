// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { DOMAIN } from '../../core/projects/core.interface';
import * as canvasUtils from '../../shared/canvas-utils';
import { getMockedScreenshot } from '../../test-utils/mocked-items-factory/mocked-camera';
import { getMockedTask } from '../../test-utils/mocked-items-factory/mocked-tasks';
import { UserCameraPermission } from '../camera-support/camera.interface';
import {
    getFileFromImage,
    getSingleValidTask,
    getSortingHandler,
    hasPermissionsDenied,
    isClassificationOrAnomaly,
    SortingOptions,
} from './util';

describe('camera-page utils', () => {
    it('applies filters and returns a png file', async () => {
        const spyDrawImageOnCanvas = jest.spyOn(canvasUtils, 'drawImageOnCanvas');
        const spyGetFileFromCanvas = jest.spyOn(canvasUtils, 'getFileFromCanvas');

        const { file } = await getFileFromImage('image-url');

        expect(file).toBeInstanceOf(File);
        expect(spyDrawImageOnCanvas).toHaveBeenCalledWith(expect.any(Image));
        expect(spyGetFileFromCanvas).toHaveBeenCalledWith(
            expect.any(HTMLCanvasElement),
            expect.stringContaining('.png'),
            'image/png'
        );
    });

    it('hasPermissionsDenied', () => {
        expect(hasPermissionsDenied(UserCameraPermission.ERRORED)).toBe(true);
        expect(hasPermissionsDenied(UserCameraPermission.DENIED)).toBe(true);
    });

    it('isClassificationOrAnomaly', () => {
        expect(isClassificationOrAnomaly(getMockedTask({ domain: DOMAIN.CLASSIFICATION }))).toBe(true);
        expect(isClassificationOrAnomaly(getMockedTask({ domain: DOMAIN.ANOMALY_DETECTION }))).toBe(true);
        expect(isClassificationOrAnomaly(getMockedTask({ domain: DOMAIN.ANOMALY_SEGMENTATION }))).toBe(true);
        expect(isClassificationOrAnomaly(getMockedTask({ domain: DOMAIN.ANOMALY_CLASSIFICATION }))).toBe(true);
    });

    it('getSingleValidTask', () => {
        expect(getSingleValidTask([getMockedTask({ domain: DOMAIN.DETECTION })])).toEqual([]);
        expect(getSingleValidTask([getMockedTask({ domain: DOMAIN.SEGMENTATION })])).toEqual([]);
        expect(
            getSingleValidTask([
                getMockedTask({ domain: DOMAIN.DETECTION }),
                getMockedTask({ domain: DOMAIN.CLASSIFICATION }),
            ])
        ).toEqual([]);
    });

    describe('getSortingHandler', () => {
        it('invalid/valid keys', () => {
            expect(getSortingHandler('' as SortingOptions)).toBeFalsy();
            expect(getSortingHandler(SortingOptions.LABEL_NAME_A_Z)).toBeTruthy();
        });

        const mockedScreenshot = [
            getMockedScreenshot({ labelName: 'b', lastModified: 1 }),
            getMockedScreenshot({ labelName: 'a', lastModified: 10 }),
            getMockedScreenshot({ labelName: 'c', lastModified: 100 }),
        ];

        it('LABEL_NAME_A_Z', () => {
            const handler = getSortingHandler(SortingOptions.LABEL_NAME_A_Z);
            expect(handler(mockedScreenshot)).toEqual([
                expect.objectContaining({ labelName: 'a' }),
                expect.objectContaining({ labelName: 'b' }),
                expect.objectContaining({ labelName: 'c' }),
            ]);
        });

        it('LABEL_NAME_Z_A', () => {
            const handler = getSortingHandler(SortingOptions.LABEL_NAME_Z_A);
            expect(handler(mockedScreenshot)).toEqual([
                expect.objectContaining({ labelName: 'c' }),
                expect.objectContaining({ labelName: 'b' }),
                expect.objectContaining({ labelName: 'a' }),
            ]);
        });

        it('MOST_RECENT', () => {
            const handler = getSortingHandler(SortingOptions.MOST_RECENT);
            expect(handler(mockedScreenshot)).toEqual([
                expect.objectContaining({ labelName: 'c' }),
                expect.objectContaining({ labelName: 'a' }),
                expect.objectContaining({ labelName: 'b' }),
            ]);
        });
    });
});
