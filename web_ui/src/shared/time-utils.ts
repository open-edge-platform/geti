// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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
