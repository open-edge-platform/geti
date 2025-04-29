// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import groupBy from 'lodash/groupBy';

import { recursivelyAddLabel } from '../../../../../core/labels/label-resolver';
import { Label, LABEL_BEHAVIOUR } from '../../../../../core/labels/label.interface';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import {
    createNewRange,
    createRangesWhenOverlapping,
    fillRangesWithEmptyRanges,
    getLabelGroupName,
    joinRanges,
    partitionRanges,
} from './utils';

const anomalousLabel = getMockedLabel({
    id: 'anomalous',
    name: 'Anomalous',
    color: 'var(--brand-coral-cobalt)',
    behaviour: LABEL_BEHAVIOUR.ANOMALOUS,
});
const normalLabel = getMockedLabel({ id: 'normal', name: 'Normal', color: 'var(--brand-moss)' });

const LABELS = [
    normalLabel,
    anomalousLabel,
    getMockedLabel({ id: 'extra-label', name: 'Extra label', color: 'var(--brand-moss)' }),
];

const GROUP_A_PARENT_A: Label = {
    id: '66f401707118b7a8abd3be59',
    name: 'Red',
    color: '#e96115ff',
    group: 'Color',
    parentLabelId: null,
    hotkey: '',
    behaviour: 4,
    isEmpty: false,
};
const GROUP_A_A_CHILD_A: Label = {
    id: '66f401707118b7a8abd3be5a',
    name: 'Hearts',
    color: '#d7bc5eff',
    group: 'Color___Red suit',
    parentLabelId: '66f401707118b7a8abd3be59',
    hotkey: '',
    behaviour: 4,
    isEmpty: false,
};

const GROUP_A_PARENT_B: Label = {
    id: '66f401707118b7a8abd3be5c',
    name: 'Black',
    color: '#26518eff',
    group: 'Color',
    parentLabelId: null,
    hotkey: '',
    behaviour: 4,
    isEmpty: false,
};
const GROUP_A_B_CHILD_A: Label = {
    id: '66f401707118b7a8abd3be5d',
    name: 'Spades',
    color: '#c9e649ff',
    group: 'Color___Black suit',
    parentLabelId: '66f401707118b7a8abd3be5c',
    hotkey: '',
    behaviour: 4,
    isEmpty: false,
};

const GROUP_B: Label = {
    id: '66f401707118b7a8abd3be5f',
    name: '7',
    color: '#ff7d00ff',
    group: 'Values',
    parentLabelId: null,
    hotkey: '',
    behaviour: 4,
    isEmpty: false,
};

const HIERARCHICAL_LABELS: Label[] = [GROUP_A_PARENT_A, GROUP_A_A_CHILD_A, GROUP_A_PARENT_B, GROUP_B];

const [normal, anomaly, other] = LABELS;

it.each([
    // Scenario with only 1 existing range
    {
        existingRanges: [{ start: 0, end: 100, labels: [normal] }],
        newRange: { start: 50, end: 100, labels: [anomaly] },
        expectedRanges: [
            { start: 0, end: 49, labels: [normal] },
            { start: 50, end: 100, labels: [anomaly] },
        ],
        labels: LABELS,
    },
    {
        existingRanges: [
            { start: 0, end: 49, labels: [anomaly] },
            { start: 50, end: 100, labels: [normal] },
        ],
        newRange: { start: 50, end: 75, labels: [anomaly] },
        expectedRanges: [
            { start: 0, end: 75, labels: [anomaly] },
            { start: 76, end: 100, labels: [normal] },
        ],
        labels: LABELS,
    },
    {
        existingRanges: [{ start: 0, end: 100, labels: [normal] }],
        newRange: { start: 0, end: 50, labels: [anomaly] },
        expectedRanges: [
            { start: 0, end: 50, labels: [anomaly] },
            { start: 51, end: 100, labels: [normal] },
        ],
        labels: LABELS,
    },
    {
        existingRanges: [{ start: 0, end: 100, labels: [normal] }],
        newRange: { start: 25, end: 75, labels: [anomaly] },
        expectedRanges: [
            { start: 0, end: 24, labels: [normal] },
            { start: 25, end: 75, labels: [anomaly] },
            { start: 76, end: 100, labels: [normal] },
        ],
        labels: LABELS,
    },
    // Scenario with multiple existing ranges
    {
        existingRanges: [
            { start: 0, end: 10, labels: [normal] },
            { start: 11, end: 80, labels: [anomaly] },
            { start: 81, end: 100, labels: [normal] },
        ],
        newRange: { start: 25, end: 75, labels: [other] },
        expectedRanges: [
            { start: 0, end: 10, labels: [normal] },
            { start: 11, end: 24, labels: [anomaly] },
            { start: 25, end: 75, labels: [other] },
            { start: 76, end: 80, labels: [anomaly] },
            { start: 81, end: 100, labels: [normal] },
        ],
        labels: LABELS,
    },
    {
        existingRanges: [
            { start: 0, end: 10, labels: [normal] },
            { start: 11, end: 80, labels: [anomaly] },
            { start: 81, end: 100, labels: [normal] },
        ],
        newRange: { start: 25, end: 85, labels: [other] },
        expectedRanges: [
            { start: 0, end: 10, labels: [normal] },
            { start: 11, end: 24, labels: [anomaly] },
            { start: 25, end: 85, labels: [other] },
            { start: 86, end: 100, labels: [normal] },
        ],
        labels: LABELS,
    },
    // Joins ranges if they have the same label and start/end point
    {
        existingRanges: [
            { start: 0, end: 24, labels: [normal] },
            { start: 25, end: 75, labels: [anomaly] },
            { start: 76, end: 100, labels: [normal] },
        ],
        newRange: { start: 25, end: 75, labels: [normal] },
        expectedRanges: [{ start: 0, end: 100, labels: [normal] }],
        labels: LABELS,
    },
    // Check that ranges with overlap are removed if their start / end are equal to the new range
    {
        existingRanges: [
            { start: 0, end: 24, labels: [normal] },
            { start: 25, end: 75, labels: [anomaly] },
            { start: 76, end: 100, labels: [normal] },
        ],
        newRange: { start: 20, end: 75, labels: [normal] },
        expectedRanges: [{ start: 0, end: 100, labels: [normal] }],
        labels: LABELS,
    },
    {
        existingRanges: [
            { start: 0, end: 24, labels: [normal] },
            { start: 25, end: 75, labels: [anomaly] },
            { start: 76, end: 100, labels: [normal] },
        ],
        newRange: { start: 25, end: 80, labels: [normal] },
        expectedRanges: [{ start: 0, end: 100, labels: [normal] }],
        labels: LABELS,
    },
    // Adding a range
    {
        existingRanges: [],
        newRange: { start: 25, end: 80, labels: [normal] },
        expectedRanges: [{ start: 25, end: 80, labels: [normal] }],
        labels: LABELS,
    },
    {
        existingRanges: [
            {
                start: 0,
                end: 24,
                labels: [GROUP_A_PARENT_A],
            },
            {
                start: 25,
                end: 49,
                labels: [],
            },
            {
                start: 50,
                end: 75,
                labels: [GROUP_A_PARENT_A, GROUP_A_A_CHILD_A],
            },
        ],
        newRange: { start: 10, end: 60, labels: [GROUP_B] },
        expectedRanges: [
            {
                start: 0,
                end: 9,
                labels: [GROUP_A_PARENT_A],
            },
            {
                start: 10,
                end: 24,
                labels: [GROUP_A_PARENT_A, GROUP_B],
            },
            {
                start: 25,
                end: 49,
                labels: [GROUP_B],
            },
            {
                start: 50,
                end: 60,
                labels: [GROUP_A_PARENT_A, GROUP_A_A_CHILD_A, GROUP_B],
            },
            {
                start: 61,
                end: 75,
                labels: [GROUP_A_PARENT_A, GROUP_A_A_CHILD_A],
            },
        ],
        labels: HIERARCHICAL_LABELS,
    },
    {
        existingRanges: [
            {
                start: 0,
                end: 24,
                labels: [GROUP_A_PARENT_A],
            },
            {
                start: 25,
                end: 49,
                labels: [],
            },
            {
                start: 50,
                end: 75,
                labels: [GROUP_A_PARENT_A, GROUP_A_A_CHILD_A],
            },
        ],
        newRange: { start: 10, end: 60, labels: [GROUP_A_B_CHILD_A] },
        expectedRanges: [
            {
                start: 0,
                end: 9,
                labels: [GROUP_A_PARENT_A],
            },
            {
                start: 10,
                end: 60,
                labels: [GROUP_A_PARENT_B, GROUP_A_B_CHILD_A],
            },
            {
                start: 61,
                end: 75,
                labels: [GROUP_A_PARENT_A, GROUP_A_A_CHILD_A],
            },
        ],
        labels: HIERARCHICAL_LABELS,
    },
])('createNewRange', ({ existingRanges, newRange, expectedRanges, labels }) => {
    expect(
        createNewRange(
            existingRanges,
            newRange,
            (label: Label, rangeLabels: Label[]) =>
                recursivelyAddLabel(
                    rangeLabels as ReadonlyArray<Label>,
                    label,
                    labels as ReadonlyArray<Label>
                ) as Label[]
        )
    ).toEqual(expectedRanges);
});

it.each([
    {
        existingRanges: [{ start: 0, end: 100, labels: [normal] }],
        expectedRanges: [{ start: 0, end: 100, labels: [normal] }],
    },
    {
        existingRanges: [
            { start: 0, end: 50, labels: [normal] },
            { start: 51, end: 100, labels: [normal] },
        ],
        expectedRanges: [{ start: 0, end: 100, labels: [normal] }],
    },
    {
        existingRanges: [
            { start: 0, end: 50, labels: [normal] },
            { start: 51, end: 75, labels: [normal] },
            { start: 76, end: 100, labels: [anomaly] },
        ],
        expectedRanges: [
            { start: 0, end: 75, labels: [normal] },
            { start: 76, end: 100, labels: [anomaly] },
        ],
    },
    {
        existingRanges: [
            { start: 0, end: 24, labels: [normal] },
            { start: 25, end: 75, labels: [anomaly] },
            { start: 76, end: 100, labels: [anomaly] },
        ],
        expectedRanges: [
            { start: 0, end: 24, labels: [normal] },
            { start: 25, end: 100, labels: [anomaly] },
        ],
    },
    // Edge case that is not supported: the original ranges have an overlap,
    // so the resulting ranges will have an overlap as well
    {
        existingRanges: [
            { start: 0, end: 50, labels: [normal] },
            { start: 25, end: 75, labels: [anomaly] },
            { start: 76, end: 100, labels: [anomaly] },
        ],
        expectedRanges: [
            { start: 0, end: 50, labels: [normal] },
            { start: 25, end: 100, labels: [anomaly] },
        ],
    },
    // Order of the labels doesn't matter
    {
        existingRanges: [
            { start: 0, end: 50, labels: [GROUP_A_PARENT_A, GROUP_A_A_CHILD_A] },
            { start: 51, end: 75, labels: [GROUP_A_A_CHILD_A, GROUP_A_PARENT_A] },
            { start: 76, end: 100, labels: [GROUP_A_PARENT_B] },
        ],
        expectedRanges: [
            { start: 0, end: 75, labels: [GROUP_A_PARENT_A, GROUP_A_A_CHILD_A] },
            { start: 76, end: 100, labels: [GROUP_A_PARENT_B] },
        ],
    },
])('joinRanges', ({ existingRanges, expectedRanges }) => {
    expect(existingRanges.reduce(joinRanges, [])).toEqual(expectedRanges);
});

it.each([
    { existingRanges: [], frames: 100, expectedRanges: [{ start: 0, end: 100, labels: [] }] },
    {
        existingRanges: [{ start: 0, end: 100, labels: [] }],
        frames: 100,
        expectedRanges: [{ start: 0, end: 100, labels: [] }],
    },
    {
        existingRanges: [{ start: 0, end: 50, labels: [normal] }],
        frames: 100,
        expectedRanges: [
            { start: 0, end: 50, labels: [normal] },
            { start: 51, end: 100, labels: [] },
        ],
    },
    {
        existingRanges: [{ start: 51, end: 100, labels: [normal] }],
        frames: 100,
        expectedRanges: [
            { start: 0, end: 50, labels: [] },
            { start: 51, end: 100, labels: [normal] },
        ],
    },
    {
        existingRanges: [
            { start: 20, end: 30, labels: [normal] },
            { start: 31, end: 40, labels: [anomaly] },
            { start: 60, end: 80, labels: [normal] },
            { start: 90, end: 98, labels: [anomaly] },
        ],
        frames: 100,
        expectedRanges: [
            { start: 0, end: 19, labels: [] },
            { start: 20, end: 30, labels: [normal] },
            { start: 31, end: 40, labels: [anomaly] },
            { start: 41, end: 59, labels: [] },
            { start: 60, end: 80, labels: [normal] },
            { start: 81, end: 89, labels: [] },
            { start: 90, end: 98, labels: [anomaly] },
            { start: 99, end: 100, labels: [] },
        ],
    },
])('fillRangesWithEmptyRanges', ({ existingRanges, expectedRanges, frames }) => {
    expect(fillRangesWithEmptyRanges(existingRanges, frames)).toEqual(expectedRanges);
});

it.each([
    {
        existingRanges: [{ start: 0, end: 100, labels: [] }],
        newRange: { start: 0, end: 50, labels: [GROUP_A_PARENT_A] },
        expectedRanges: [
            { start: 0, end: 50, labels: [GROUP_A_PARENT_A] },
            { start: 51, end: 100, labels: [] },
        ],
        labels: HIERARCHICAL_LABELS,
    },
    {
        existingRanges: [
            { start: 0, end: 20, labels: [GROUP_A_PARENT_A] },
            { start: 21, end: 100, labels: [] },
        ],
        newRange: { start: 10, end: 50, labels: [GROUP_A_A_CHILD_A] },
        expectedRanges: [
            { start: 0, end: 9, labels: [GROUP_A_PARENT_A] },
            { start: 10, end: 20, labels: [GROUP_A_PARENT_A, GROUP_A_A_CHILD_A] },
            { start: 21, end: 50, labels: [GROUP_A_PARENT_A, GROUP_A_A_CHILD_A] },
            { start: 51, end: 100, labels: [] },
        ],
        labels: HIERARCHICAL_LABELS,
    },
    {
        existingRanges: [
            { start: 0, end: 20, labels: [] },
            { start: 21, end: 50, labels: [GROUP_A_PARENT_A] },
            { start: 51, end: 100, labels: [] },
        ],
        newRange: { start: 30, end: 40, labels: [GROUP_A_A_CHILD_A] },
        expectedRanges: [
            { start: 21, end: 29, labels: [GROUP_A_PARENT_A] },
            { start: 30, end: 40, labels: [GROUP_A_PARENT_A, GROUP_A_A_CHILD_A] },
            { start: 41, end: 50, labels: [GROUP_A_PARENT_A] },
        ],
        labels: HIERARCHICAL_LABELS,
    },
    {
        existingRanges: [
            { start: 0, end: 20, labels: [] },
            { start: 21, end: 50, labels: [GROUP_A_PARENT_A] },
            { start: 51, end: 100, labels: [] },
        ],
        newRange: { start: 30, end: 40, labels: [GROUP_A_PARENT_B] },
        expectedRanges: [
            { start: 21, end: 29, labels: [GROUP_A_PARENT_A] },
            { start: 30, end: 40, labels: [GROUP_A_PARENT_B] },
            { start: 41, end: 50, labels: [GROUP_A_PARENT_A] },
        ],
        labels: HIERARCHICAL_LABELS,
    },
    {
        existingRanges: [
            { start: 0, end: 20, labels: [GROUP_A_PARENT_A] },
            { start: 21, end: 100, labels: [] },
        ],
        newRange: { start: 21, end: 40, labels: [GROUP_A_PARENT_B] },
        expectedRanges: [
            { start: 21, end: 40, labels: [GROUP_A_PARENT_B] },
            { start: 41, end: 100, labels: [] },
        ],
        labels: HIERARCHICAL_LABELS,
    },
    {
        existingRanges: [
            { start: 0, end: 20, labels: [GROUP_A_PARENT_A] },
            { start: 21, end: 50, labels: [GROUP_A_PARENT_B] },
            { start: 51, end: 60, labels: [] },
            { start: 61, end: 70, labels: [GROUP_B] },
            { start: 71, end: 85, labels: [GROUP_A_PARENT_B, GROUP_A_B_CHILD_A] },
            { start: 86, end: 100, labels: [] },
        ],
        newRange: { start: 15, end: 90, labels: [GROUP_A_A_CHILD_A] },
        expectedRanges: [
            { start: 0, end: 14, labels: [GROUP_A_PARENT_A] },
            { start: 15, end: 20, labels: [GROUP_A_PARENT_A, GROUP_A_A_CHILD_A] },
            { start: 21, end: 50, labels: [GROUP_A_PARENT_A, GROUP_A_A_CHILD_A] },
            { start: 51, end: 60, labels: [GROUP_A_PARENT_A, GROUP_A_A_CHILD_A] },
            { start: 61, end: 70, labels: [GROUP_B, GROUP_A_PARENT_A, GROUP_A_A_CHILD_A] },
            { start: 71, end: 85, labels: [GROUP_A_PARENT_A, GROUP_A_A_CHILD_A] },
            { start: 86, end: 90, labels: [GROUP_A_PARENT_A, GROUP_A_A_CHILD_A] },
            { start: 91, end: 100, labels: [] },
        ],
        labels: HIERARCHICAL_LABELS,
    },
])('createRangesWhenOverlapping', ({ existingRanges, expectedRanges, newRange, labels }) => {
    const { rangesWithOverlap } = partitionRanges(existingRanges, newRange);

    expect(
        createRangesWhenOverlapping(
            rangesWithOverlap,
            newRange,
            (label: Label, rangeLabels: Label[]) =>
                recursivelyAddLabel(
                    rangeLabels as ReadonlyArray<Label>,
                    label,
                    labels as ReadonlyArray<Label>
                ) as Label[]
        )
    ).toEqual(expectedRanges);
});

it.each([
    {
        existingRanges: [
            { start: 0, end: 10, labels: [] },
            { start: 20, end: 30, labels: [] },
        ],
        range: { start: 40, end: 50, labels: [] },
        expectedRanges: {
            rangesBeforeRange: [
                { start: 0, end: 10, labels: [] },
                { start: 20, end: 30, labels: [] },
            ],
            rangesWithOverlap: [],
            rangesAfterRange: [],
        },
    },
    {
        existingRanges: [
            { start: 0, end: 10, labels: [] },
            { start: 20, end: 30, labels: [] },
        ],
        range: { start: 5, end: 25, labels: [] },
        expectedRanges: {
            rangesBeforeRange: [],
            rangesWithOverlap: [
                { start: 0, end: 10, labels: [] },
                { start: 20, end: 30, labels: [] },
            ],
            rangesAfterRange: [],
        },
    },
    {
        existingRanges: [
            { start: 0, end: 10, labels: [] },
            { start: 20, end: 30, labels: [] },
        ],
        range: { start: 11, end: 19, labels: [] },
        expectedRanges: {
            rangesBeforeRange: [{ start: 0, end: 10, labels: [] }],
            rangesWithOverlap: [],
            rangesAfterRange: [{ start: 20, end: 30, labels: [] }],
        },
    },
    {
        existingRanges: [
            { start: 0, end: 10, labels: [] },
            { start: 20, end: 30, labels: [] },
        ],
        range: { start: 20, end: 30, labels: [] },
        expectedRanges: {
            rangesBeforeRange: [{ start: 0, end: 10, labels: [] }],
            rangesWithOverlap: [{ start: 20, end: 30, labels: [] }],
            rangesAfterRange: [],
        },
    },
    {
        existingRanges: [
            { start: 0, end: 10, labels: [] },
            { start: 20, end: 30, labels: [] },
        ],
        range: { start: 31, end: 40, labels: [] },
        expectedRanges: {
            rangesBeforeRange: [
                { start: 0, end: 10, labels: [] },
                { start: 20, end: 30, labels: [] },
            ],
            rangesWithOverlap: [],
            rangesAfterRange: [],
        },
    },
    {
        existingRanges: [
            { start: 10, end: 20, labels: [] },
            { start: 30, end: 40, labels: [] },
        ],
        range: { start: 0, end: 9, labels: [] },
        expectedRanges: {
            rangesBeforeRange: [],
            rangesWithOverlap: [],
            rangesAfterRange: [
                { start: 10, end: 20, labels: [] },
                { start: 30, end: 40, labels: [] },
            ],
        },
    },
])('partitionRanges', ({ existingRanges, range, expectedRanges }) => {
    expect(partitionRanges(existingRanges, range)).toEqual(expectedRanges);
});

describe('getLabelGroupName', () => {
    it('returns group name when there is only one group', () => {
        const labels = [
            getMockedLabel({
                id: '1',
                group: 'Classification labels',
                name: 'heart',
            }),
            getMockedLabel({
                id: '2',
                group: 'Classification labels',
                name: 'spade',
            }),
        ];

        const groupedLabels = groupBy(labels, 'group');

        expect(getLabelGroupName(groupedLabels, 0)).toBe('Classification labels');
    });

    it('returns "Anomaly labels" when there are anomaly labels', () => {
        const labels = [normalLabel, anomalousLabel];

        const groupedLabels = groupBy(labels, 'group');
        expect(getLabelGroupName(groupedLabels, 0)).toBe('Anomaly labels');
    });

    it("returns the group name when there are multiple groups and group name includes label's name", () => {
        const labels = [
            getMockedLabel({
                id: '1',
                group: 'Classification labels___heart',
                name: 'heart',
            }),
            getMockedLabel({
                id: '2',
                group: 'Classification labels___ace',
                name: 'ace',
            }),
        ];

        const groupedLabels = groupBy(labels, 'group');

        labels.forEach((label, index) => {
            expect(getLabelGroupName(groupedLabels, index)).toBe(label.name);
        });
    });

    it('returns the label name when there are multiple groups and group name does not include label name', () => {
        const labelWithCorrectGroupName = getMockedLabel({
            id: '1',
            group: 'Classification labels___heart',
            name: 'heart',
        });
        const labelWithDifferentGroupName = getMockedLabel({
            id: '2',
            group: 'Classification labels___ace',
            name: 'yolo',
        });

        const labels = [labelWithCorrectGroupName, labelWithDifferentGroupName];
        const groupedLabels = groupBy(labels, 'group');

        labels.forEach((label, index) => {
            expect(getLabelGroupName(groupedLabels, index)).toBe(label.name);
        });
    });
});
