// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.
interface TimeUnits {
    hours: number;
    minutes: number;
    seconds: number;
}

export const getTimeUnits = (duration: number): TimeUnits => {
    const hours = Math.floor(duration / (60 * 60));
    const hoursSeconds = hours * 60 * 60;

    const minutes = Math.floor((duration - hoursSeconds) / 60);
    const minutesSeconds = 60 * minutes;

    const seconds = duration - hoursSeconds - minutesSeconds;

    return { hours, minutes, seconds };
};

export const paddedString = (number: number): string => Math.floor(number).toString().padStart(2, '0');

export const isFormattedHourMinSec = (val: string): boolean => /^[0-9]{2}:[0-9]{2}:[0-9]{2}$/.test(val);

export const formatToHourMinSec = (duration: number): string => {
    const { hours, minutes, seconds } = getTimeUnits(duration);

    return `${paddedString(hours)}:${paddedString(minutes)}:${paddedString(seconds)}`;
};
