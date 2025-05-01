// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getIds } from '@shared/utils';
import isEmpty from 'lodash/isEmpty';
import isEqual from 'lodash/isEqual';

import { LabeledVideoRange } from '../../../../../core/annotations/labeled-video-range.interface';
import { Label } from '../../../../../core/labels/label.interface';
import { GROUP_SEPARATOR, isAnomalous } from '../../../../../core/labels/utils';

export const joinRanges = (ranges: LabeledVideoRange[], range: LabeledVideoRange, idx: number) => {
    const lastRange = ranges.at(-1);

    if (
        lastRange !== undefined &&
        idx > 0 &&
        lastRange.end + 1 === range.start &&
        isEqual(new Set(getIds(lastRange.labels)), new Set(getIds(range.labels)))
    ) {
        return [...ranges.slice(0, -1), { ...lastRange, end: range.end }];
    }

    return [...ranges, range];
};

export const partitionRanges = (ranges: LabeledVideoRange[], range: LabeledVideoRange) => {
    const rangesBeforeRange = ranges.filter(({ start, end }) => {
        return start < range.start && end < range.start;
    });

    const rangesAfterRange = ranges.filter(({ start, end }) => {
        return start > range.end && end > range.end;
    });

    const rangesWithOverlap = ranges.filter(({ start, end }) => {
        if (start < range.start && end < range.start) {
            return false;
        }
        if (start > range.end && end > range.end) {
            return false;
        }

        return true;
    });

    return { rangesBeforeRange, rangesAfterRange, rangesWithOverlap };
};

export const fillRangesWithEmptyRanges = (ranges: LabeledVideoRange[], frames: number): LabeledVideoRange[] => {
    const initialRanges: LabeledVideoRange[] = [{ start: 0, end: frames, labels: [] }];
    if (isEmpty(ranges)) {
        return initialRanges;
    }

    const rangesFilledWithEmptyRanges = ranges.reduce<LabeledVideoRange[]>((allRanges, range, idx) => {
        if (idx === 0 && range.start !== 0) {
            allRanges.push({ start: 0, end: range.start - 1, labels: [] }, range);

            return allRanges;
        }

        const previousRange = allRanges.at(-1);
        if (previousRange === undefined) {
            allRanges.push(range);

            return allRanges;
        }

        if (previousRange.end + 1 !== range.start) {
            allRanges.push({ start: previousRange.end + 1, end: range.start - 1, labels: [] }, range);
            return allRanges;
        }

        allRanges.push(range);
        return allRanges;
    }, []);

    const lastRange = rangesFilledWithEmptyRanges.at(-1);

    if (lastRange !== undefined && lastRange.end !== frames) {
        rangesFilledWithEmptyRanges.push({ start: lastRange.end + 1, end: frames, labels: [] });
    }

    return rangesFilledWithEmptyRanges;
};

const createRangesWhenNewRangeIsInsideOtherRange = (
    range: LabeledVideoRange,
    currentRange: LabeledVideoRange,
    resolveLabels: (label: Label, rangeLabels: Label[]) => Label[]
): LabeledVideoRange[] => {
    const rangeLabel = range.labels[0];

    if (range.start > currentRange.start && range.end < currentRange.end) {
        const newRangeFirstPart: LabeledVideoRange = {
            ...currentRange,
            end: range.start - 1,
        };
        const newRangeSecondPart: LabeledVideoRange = {
            ...currentRange,
            start: range.end + 1,
        };

        return [
            newRangeFirstPart,
            {
                ...range,
                labels: resolveLabels(rangeLabel, currentRange.labels),
            },
            newRangeSecondPart,
        ];
    }

    if (range.start === currentRange.start && range.end === currentRange.end) {
        return [
            {
                ...range,
                labels: resolveLabels(rangeLabel, currentRange.labels),
            },
        ];
    }

    if (range.start === currentRange.start) {
        const newRange: LabeledVideoRange = { ...currentRange, start: range.end + 1 };

        return [
            {
                ...range,
                labels: resolveLabels(rangeLabel, currentRange.labels),
            },
            newRange,
        ];
    }

    const newRange: LabeledVideoRange = { ...currentRange, end: range.start - 1 };

    return [
        newRange,
        {
            ...range,
            labels: resolveLabels(rangeLabel, currentRange.labels),
        },
    ];
};

const createRangesWhenNewRangeStartsInsideAndEndsOutside = (
    range: LabeledVideoRange,
    currentRange: LabeledVideoRange,
    resolveLabels: (label: Label, rangeLabels: Label[]) => Label[]
): LabeledVideoRange[] => {
    const rangeLabel = range.labels[0];

    // range will be added together with the next overlapping item
    if (range.start === currentRange.end) {
        return [currentRange];
    }

    const newRangeFirstPart: LabeledVideoRange = {
        ...currentRange,
        end: range.start - 1,
    };
    const newRangeSecondPart: LabeledVideoRange = {
        ...range,
        end: currentRange.end,
        labels: resolveLabels(rangeLabel, currentRange.labels),
    };

    return [newRangeFirstPart, newRangeSecondPart];
};

const createRangesNewRangeOverlapsWholeCurrentRange = (
    range: LabeledVideoRange,
    currentRange: LabeledVideoRange,
    resolveLabels: (label: Label, rangeLabels: Label[]) => Label[]
): LabeledVideoRange[] => {
    const rangeLabel = range.labels[0];

    const newRage: LabeledVideoRange = {
        ...currentRange,
        labels: resolveLabels(rangeLabel, currentRange.labels),
    };

    return [newRage];
};

const createRangesNewRangeStartsBeforeEndsInsideCurrentRange = (
    range: LabeledVideoRange,
    currentRange: LabeledVideoRange,
    resolveLabels: (label: Label, rangeLabels: Label[]) => Label[]
): LabeledVideoRange[] => {
    const rangeLabel = range.labels[0];

    const newRangeFirstPart: LabeledVideoRange = {
        ...range,
        start: currentRange.start,
        labels: resolveLabels(rangeLabel, currentRange.labels),
    };
    const newRangeSecondPart: LabeledVideoRange = { ...currentRange, start: range.end + 1 };

    return [newRangeFirstPart, newRangeSecondPart];
};

export const createRangesWhenOverlapping = (
    ranges: LabeledVideoRange[],
    range: LabeledVideoRange,
    resolveLabels: (label: Label, rangeLabels: Label[]) => Label[]
) => {
    return ranges.reduce((newRanges: LabeledVideoRange[], currentRange: LabeledVideoRange) => {
        // entire range (A) is inside currentRange, other ranges (-)
        // ------[BBBBBBB]----------
        // -------[AAAA]------------
        if (range.start >= currentRange.start && range.end <= currentRange.end) {
            newRanges.push(...createRangesWhenNewRangeIsInsideOtherRange(range, currentRange, resolveLabels));

            return newRanges;
        }

        // range starts inside the currentRange but ends outside
        // ------[BBBBBBB]----------
        // --------[AAAAAAAAA]---
        if (range.start >= currentRange.start && range.end >= currentRange.end) {
            newRanges.push(...createRangesWhenNewRangeStartsInsideAndEndsOutside(range, currentRange, resolveLabels));

            return newRanges;
        }

        // range starts before the currentRange and ends after
        // ------[BBBBBBB]----------
        // -----[AAAAAAAAA]---------
        if (range.start <= currentRange.start && range.end >= currentRange.end) {
            newRanges.push(...createRangesNewRangeOverlapsWholeCurrentRange(range, currentRange, resolveLabels));

            return newRanges;
        }

        // range starts before the currentRange and ends inside
        // ------[BBBBBBB]----------
        // -----[AAAA]--------------
        if (range.start <= currentRange.start && range.end <= currentRange.end) {
            newRanges.push(
                ...createRangesNewRangeStartsBeforeEndsInsideCurrentRange(range, currentRange, resolveLabels)
            );

            return newRanges;
        }

        return newRanges;
    }, []);
};

export const createNewRange = (
    oldRanges: LabeledVideoRange[],
    range: LabeledVideoRange,
    resolveLabels: (label: Label, rangeLabels: Label[]) => Label[]
): LabeledVideoRange[] => {
    const { rangesBeforeRange, rangesWithOverlap, rangesAfterRange } = partitionRanges(oldRanges, range);

    let newRanges: LabeledVideoRange[];
    if (isEmpty(rangesWithOverlap)) {
        newRanges = [range];
    } else {
        newRanges = createRangesWhenOverlapping(rangesWithOverlap, range, resolveLabels);
    }
    // Remove edges if they end up with a nonzero width
    const rangesInOverlap = newRanges.filter(({ start, end }) => end > start);

    return [...rangesBeforeRange, ...rangesInOverlap, ...rangesAfterRange].reduce(joinRanges, []);
};

export const getLabelGroupName = (groupedLabels: Record<string, Label[]>, index: number): string => {
    const groupNames = Object.keys(groupedLabels);

    if (groupNames.length === 1) {
        const isAnomaly = groupedLabels[groupNames[0]].some(isAnomalous);

        if (isAnomaly) {
            return 'Anomaly labels';
        }
    }

    const currentGroupNameRaw = groupNames[index];
    const labels = groupedLabels[currentGroupNameRaw];

    // Example: Get "heart" part from "Classification labels___heart"
    const currentGroupName = currentGroupNameRaw.split(GROUP_SEPARATOR).at(-1) ?? currentGroupNameRaw;

    if (labels.length === 1) {
        return labels[0].name;
    }

    return currentGroupName;
};
