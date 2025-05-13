// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isNil, uniqBy } from 'lodash-es';

export const isVideoInput = (mediaDevice: MediaDeviceInfo) => mediaDevice.kind === 'videoinput';

export const getVideoUserMedia = () => navigator.mediaDevices.getUserMedia({ video: true });

export const getVideoDevices = async () => {
    const devices = await navigator.mediaDevices.enumerateDevices();

    const videoDevices = devices.filter(isVideoInput);

    return uniqBy(videoDevices, (device) => device.deviceId);
};

export const getEstimateFreeStorage = async () => {
    try {
        const estimate = await navigator.storage.estimate();

        if (isNil(estimate?.usage) || isNil(estimate?.quota)) {
            return NaN;
        }

        return estimate.quota - estimate.usage;
    } catch (_error: unknown) {
        return NaN;
    }
};

export const getBrowserConstraints = () => navigator.mediaDevices.getSupportedConstraints();
