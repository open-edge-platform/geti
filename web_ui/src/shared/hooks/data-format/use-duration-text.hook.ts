// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getTimeUnits, paddedString } from '../../time-utils';

export const useDurationText = (duration: number, showHours = true): string => {
    const { hours, minutes, seconds } = getTimeUnits(duration);

    return showHours
        ? `${paddedString(hours)}:${paddedString(minutes)}:${paddedString(seconds)}`
        : `${paddedString(minutes)}:${paddedString(seconds)}`;
};
