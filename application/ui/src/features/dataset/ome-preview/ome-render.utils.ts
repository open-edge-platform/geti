// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { OmeChannelDisplaySetting, OmeImageInfo } from '@/api/types';

// Largest side rendered by the annotator; larger images are displayed from a lower pyramid level when available
export const MAX_RENDERED_SIDE = 8192;

// Picks the most detailed pyramid level that fits in `maxSide`, or the least detailed one if none does.
export const getRenderLevel = (info: Pick<OmeImageInfo, 'pyramid_levels'>, maxSide = MAX_RENDERED_SIDE): number => {
    const levels = info.pyramid_levels;

    if (levels.length === 0) {
        return 0;
    }

    const fittingLevel = levels.find(({ width, height }) => Math.max(width, height) <= maxSide);

    return fittingLevel?.level ?? levels[levels.length - 1].level;
};

// Short, stable token identifying channel display settings, so that a re-render is fetched whenever they change.
export const getRenderVersion = (settings: OmeChannelDisplaySetting[]): string => {
    const text = JSON.stringify(
        settings.map(({ channel, target, enabled, window_min, window_max }) => [
            channel,
            target,
            enabled,
            window_min,
            window_max,
        ])
    );
    let hash = 5381;

    for (let index = 0; index < text.length; index++) {
        hash = ((hash << 5) + hash + text.charCodeAt(index)) | 0;
    }

    return (hash >>> 0).toString(36);
};

const BITS_BY_PIXEL_TYPE: Record<string, number> = {
    uint8: 8,
    uint16: 16,
    uint32: 32,
    int8: 7,
    int16: 15,
    int32: 31,
};

// Range a channel value can take according to the image metadata; used as the bounds of the display range slider.
export const getDeclaredValueRange = (
    info: Pick<OmeImageInfo, 'pixel_type' | 'significant_bits'>,
    settings: OmeChannelDisplaySetting[]
): { min: number; max: number } => {
    const bits = info.significant_bits ?? BITS_BY_PIXEL_TYPE[info.pixel_type];

    if (bits !== undefined) {
        const isSigned = info.pixel_type.startsWith('int');

        return { min: isSigned ? -(2 ** bits) : 0, max: 2 ** bits - 1 };
    }

    // Floating point images declare no range: allow some headroom around the current windows
    const windowMax = Math.max(1, ...settings.map(({ window_max }) => window_max));
    const windowMin = Math.min(0, ...settings.map(({ window_min }) => window_min));

    return { min: windowMin, max: windowMax * 2 };
};
