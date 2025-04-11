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

import { isIPad, isIPhone } from '@react-aria/utils';

import { getBrowserConstraints, getVideoUserMedia } from '../../../shared/navigator-utils';
import { UserCameraPermission, UserCameraPermissionError } from '../../camera-support/camera.interface';
import {
    applySettings,
    getBrowserPermissions,
    getInvalidKeyCapabilities,
    getPermissionError,
    getValidCapabilities,
    isDesktop,
    mergeSettingAndCapabilities,
    removeInvalidCapabilities,
} from './util';

jest.mock('../../../shared/navigator-utils', () => ({
    ...jest.requireActual('../../../shared/navigator-utils'),
    getVideoUserMedia: jest.fn(),
    getBrowserConstraints: jest.fn(),
}));

jest.mock('@react-aria/utils', () => ({
    ...jest.requireActual('@react-aria/utils'),
    isIPad: jest.fn(),
    isIPhone: jest.fn(),
}));

describe('camera providers utils', () => {
    it('isDesktop', () => {
        isDesktop();

        expect(isIPad).toHaveBeenCalled();
        expect(isIPhone).toHaveBeenCalled();
    });

    it('removeInvalidCapabilities', () => {
        const mockedCapabilities = {
            aspectRatio: { max: 4096, min: 1 },
            deviceId: 'd4dbd841baf63565b4f3f8fb217e60fbce531cb85d5c8c0979da9a8e033367ef',
            facingMode: [],
            frameRate: { max: 2, min: 1 },
            groupId: 'a1ea27b469dd1b0cd6a4819911cb78316e5579373d537a0db1d6bd9ffef91900',
            resizeMode: ['none', 'crop-and-scale'],
        };

        expect(removeInvalidCapabilities(mockedCapabilities, ['aspectRatio', 'deviceId', 'groupId'])).toEqual({
            facingMode: [],
            frameRate: { max: 2, min: 1 },
            resizeMode: ['none', 'crop-and-scale'],
        });
    });

    it('applySettings', () => {
        const options = { aspectRatio: 1 };
        const mockedMediaStreamTrack = {
            applyConstraints: jest.fn(),
        } as unknown as MediaStreamTrack;

        const mockedStream = {
            getVideoTracks: jest.fn(() => [mockedMediaStreamTrack]),
        } as unknown as MediaStream;

        applySettings(mockedStream, options);

        expect(mockedStream.getVideoTracks).toHaveBeenCalled();
        expect(mockedMediaStreamTrack.applyConstraints).toHaveBeenCalledWith({ advanced: [options] });
    });

    describe('getInvalidKeyCapabilities', () => {
        beforeEach(() => {
            jest.mocked(isIPad).mockReturnValue(false);
            jest.mocked(isIPhone).mockReturnValue(false);
        });

        it('desktop', () => {
            expect(getInvalidKeyCapabilities()).toContain('facingMode');
        });

        it('mobile', () => {
            jest.mocked(isIPhone).mockReturnValue(true);
            expect(getInvalidKeyCapabilities()).not.toContain('facingMode');
        });

        it('isIPad', () => {
            jest.mocked(isIPad).mockReturnValue(true);
            expect(getInvalidKeyCapabilities()).not.toContain('facingMode');
        });
    });

    it('getValidCapabilities', () => {
        const constrains = {
            width: true,
            height: true,
            resizeMode: false,
            aspectRatio: false,
        };

        const deviceCapabilities = {
            width: { max: 20, min: 1 },
            height: { max: 20, min: 1 },
            facingMode: [],
            deviceId: '63614d3ea4209ecb8adadad4936b12bd4d8c96642428ac34cde001225abe002a',
        };

        jest.mocked(getBrowserConstraints).mockReturnValue(constrains);

        expect(getValidCapabilities(deviceCapabilities)).toEqual({
            width: { max: 20, min: 1 },
            height: { max: 20, min: 1 },
        });
    });

    describe('mergeSettingAndCapabilities', () => {
        it('min max', () => {
            expect(mergeSettingAndCapabilities({ width: { max: 1920, min: 1 } }, { width: 640 })).toEqual([
                { config: { max: 1920, min: 1, type: 'minMax', value: 640 }, name: 'width' },
            ]);
        });

        it('options', () => {
            const settings = { resizeMode: 'none' } as MediaTrackSettings;
            const capabilities = { resizeMode: ['none', 'crop-and-scale'] } as MediaTrackCapabilities;

            expect(mergeSettingAndCapabilities(capabilities, settings)).toEqual([
                {
                    name: 'resizeMode',
                    config: { options: ['none', 'crop-and-scale'], type: 'selection', value: 'none' },
                },
            ]);
        });
    });

    it('getPermissionError', () => {
        expect(getPermissionError('')).toBe(UserCameraPermission.ERRORED);
        expect(getPermissionError(Error(UserCameraPermissionError.NOT_ALLOWED))).toBe(UserCameraPermission.DENIED);
    });

    describe('getBrowserPermissions', () => {
        it('granted', () => {
            const mockedStream = {} as MediaStream;
            jest.mocked(getVideoUserMedia).mockResolvedValue(mockedStream);

            return expect(getBrowserPermissions()).resolves.toEqual({
                permissions: UserCameraPermission.GRANTED,
                stream: mockedStream,
            });
        });

        it('error', () => {
            jest.mocked(getVideoUserMedia).mockRejectedValue('');

            return expect(getBrowserPermissions()).resolves.toEqual({
                permissions: UserCameraPermission.ERRORED,
                stream: null,
            });
        });
    });
});
