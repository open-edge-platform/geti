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

import { getEstimateFreeStorage, getVideoDevices, isVideoInput } from './navigator-utils';

const getNavigatorConfig = (property: string, methods: object) => {
    Object.defineProperty(global.navigator, property, {
        value: {
            // eslint-disable-next-line @typescript-eslint/ban-ts-comment
            // @ts-ignore
            ...global.navigator[property],
            ...methods,
        },
    });
};

const getMockedMediaDevice = (props: Partial<MediaDeviceInfo>): MediaDeviceInfo => ({
    label: '',
    kind: 'videoinput',
    groupId: 'groupId-test',
    deviceId: 'deviceId-test',
    toJSON: jest.fn(),
    ...props,
});

describe('navigator utils', () => {
    describe('getEstimateFreeStorage', () => {
        const mockedEstimate = jest.fn();
        getNavigatorConfig('storage', { estimate: mockedEstimate });

        it('low space', () => {
            mockedEstimate.mockResolvedValue({ usage: 10_000, quota: 10_000 });
            return expect(getEstimateFreeStorage()).resolves.toBe(0);
        });

        it('falsy response', () => {
            mockedEstimate.mockResolvedValue({ usage: undefined, quota: undefined });

            return expect(getEstimateFreeStorage()).resolves.toBe(NaN);
        });

        it('response error', () => {
            mockedEstimate.mockRejectedValue('');

            return expect(getEstimateFreeStorage()).resolves.toBe(NaN);
        });
    });

    it('isVideoInput', () => {
        expect(isVideoInput(getMockedMediaDevice({ kind: 'videoinput' }))).toBe(true);
        expect(isVideoInput(getMockedMediaDevice({ kind: 'audioinput' }))).toBe(false);
        expect(isVideoInput(getMockedMediaDevice({ kind: 'audiooutput' }))).toBe(false);
    });

    describe('getVideoDevices', () => {
        const mockedEnumerateDevices = jest.fn();
        beforeAll(() => {
            Object.defineProperty(global.navigator, 'mediaDevices', {
                value: {
                    enumerateDevices: mockedEnumerateDevices,
                },
            });
        });

        it('getVideoDevices', () => {
            mockedEnumerateDevices.mockResolvedValue([
                getMockedMediaDevice({ kind: 'videoinput' }),
                getMockedMediaDevice({ kind: 'audioinput' }),
                getMockedMediaDevice({ kind: 'audiooutput' }),
            ]);

            return expect(getVideoDevices()).resolves.toHaveLength(1);
        });

        it('getVideoDevices does not return duplicated device ids', () => {
            mockedEnumerateDevices.mockResolvedValue([
                getMockedMediaDevice({ kind: 'videoinput' }),
                getMockedMediaDevice({ kind: 'videoinput' }),
                getMockedMediaDevice({ kind: 'audioinput' }),
                getMockedMediaDevice({ kind: 'audiooutput' }),
            ]);

            return expect(getVideoDevices()).resolves.toHaveLength(1);
        });
    });
});
