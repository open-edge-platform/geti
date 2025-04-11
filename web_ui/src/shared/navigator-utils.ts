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

import isNil from 'lodash/isNil';
import uniqBy from 'lodash/uniqBy';

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
