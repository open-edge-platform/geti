// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isIPad, isIPhone } from '@react-aria/utils';
import { omit, pick } from 'lodash-es';

import { getBrowserConstraints, getVideoUserMedia } from '../../../shared/navigator-utils';
import { isNonEmptyArray } from '../../../shared/utils';
import { UserCameraPermission, UserCameraPermissionError } from '../../camera-support/camera.interface';

const INVALID_CAPABILITIES: CapabilitiesKeys[] = ['groupId', 'deviceId', 'aspectRatio'];

type CapabilitiesKeys = keyof MediaTrackCapabilities;
export type SettingMinMax = { type: 'minMax'; max: number; min: number; value: number };
export type SettingSelection = { type: 'selection'; options: string[]; value: string };
export interface DeviceConfiguration {
    name: string;
    config: SettingMinMax | SettingSelection;
}

export const isDesktop = () => !isIPhone() && !isIPad();

export const removeInvalidCapabilities = (
    capabilities: MediaTrackCapabilities,
    toRemove: CapabilitiesKeys[]
): MediaTrackCapabilities => {
    const newCapabilities = { ...capabilities };

    toRemove.forEach((name) => {
        newCapabilities[name] && delete newCapabilities[name];
    });

    return newCapabilities;
};

export const applySettings = (stream: MediaStream, options: MediaTrackConstraintSet) => {
    const [videoTrack] = stream.getVideoTracks();
    videoTrack.applyConstraints({ advanced: [options] });
};

const getBrowserValidCapabilities = () => {
    return Object.entries(getBrowserConstraints())
        .filter(([_key, isValid]) => isValid)
        .map(([key]) => key as CapabilitiesKeys);
};

export const getInvalidKeyCapabilities = (): CapabilitiesKeys[] => {
    return isDesktop() ? [...INVALID_CAPABILITIES, 'facingMode'] : INVALID_CAPABILITIES;
};

export const getValidCapabilities = (capabilities: MediaTrackCapabilities) => {
    const filteredBrowserCapabilities = pick(capabilities, getBrowserValidCapabilities());
    return omit(filteredBrowserCapabilities, getInvalidKeyCapabilities());
};

export const mergeSettingAndCapabilities = (
    capabilities: MediaTrackCapabilities,
    settings: MediaTrackSettings
): DeviceConfiguration[] =>
    Object.entries(capabilities).map(([name, options]) => {
        const value = settings[name as keyof MediaTrackSettings];

        return {
            name,
            config: isNonEmptyArray(options)
                ? ({ type: 'selection', value, options } as SettingSelection)
                : ({ type: 'minMax', value, ...(options as object) } as SettingMinMax),
        };
    });

export const getPermissionError = (error: unknown) => {
    const errorType = error instanceof Error ? error.message : '';

    return errorType === UserCameraPermissionError.NOT_ALLOWED
        ? UserCameraPermission.DENIED
        : UserCameraPermission.ERRORED;
};

export const getBrowserPermissions = async () => {
    try {
        const stream = await getVideoUserMedia();
        return { permissions: UserCameraPermission.GRANTED, stream };
    } catch (error: unknown) {
        return { permissions: getPermissionError(error), stream: null };
    }
};
