// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DOMAIN } from '../../core/projects/core.interface';
import { getMockedScreenshot } from '../../test-utils/mocked-items-factory/mocked-camera';
import { getMockedTask } from '../../test-utils/mocked-items-factory/mocked-tasks';
import { UserCameraPermission } from '../camera-support/camera.interface';
import {
    getSingleValidTask,
    getSortingHandler,
    hasPermissionsDenied,
    isClassificationOrAnomaly,
    SortingOptions,
} from './util';

describe('camera-page utils', () => {
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
