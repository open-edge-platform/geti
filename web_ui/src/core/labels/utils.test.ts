// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedLabel, MOCKED_HIERARCHY } from '../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedTask } from '../../test-utils/mocked-items-factory/mocked-tasks';
import { DOMAIN } from '../projects/core.interface';
import { LabelDTO } from './dtos/label.interface';
import { Label, LABEL_BEHAVIOUR } from './label.interface';
import {
    filterOutExclusiveLabel,
    getBehaviourFromDTO,
    getFlattenedGroups,
    getFlattenedLabels,
    getNonEmptyLabelsFromProject,
    getNotEmptyLabelsFromOneTask,
    isAnomalous,
    isExclusive,
    isGlobal,
    isLocal,
} from './utils';

it.each([
    [LABEL_BEHAVIOUR.EXCLUSIVE, true],
    [LABEL_BEHAVIOUR.EXCLUSIVE + LABEL_BEHAVIOUR.LOCAL, true],
    [LABEL_BEHAVIOUR.EXCLUSIVE + LABEL_BEHAVIOUR.GLOBAL, true],
    [LABEL_BEHAVIOUR.EXCLUSIVE + LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.GLOBAL, true],
    [LABEL_BEHAVIOUR.LOCAL, false],
    [LABEL_BEHAVIOUR.GLOBAL, false],
    [LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.GLOBAL, false],
])('isExclusive(%o) === %o', (behaviour: LABEL_BEHAVIOUR, expectedResult: boolean) => {
    const label = getMockedLabel({ behaviour });

    expect(isExclusive(label)).toBe(expectedResult);
});

it.each([
    [LABEL_BEHAVIOUR.EXCLUSIVE, false],
    [LABEL_BEHAVIOUR.EXCLUSIVE + LABEL_BEHAVIOUR.LOCAL, true],
    [LABEL_BEHAVIOUR.EXCLUSIVE + LABEL_BEHAVIOUR.GLOBAL, false],
    [LABEL_BEHAVIOUR.EXCLUSIVE + LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.GLOBAL, true],
    [LABEL_BEHAVIOUR.LOCAL, true],
    [LABEL_BEHAVIOUR.GLOBAL, false],
    [LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.GLOBAL, true],
])('isLocal(%o) === %o', (behaviour: LABEL_BEHAVIOUR, expectedResult: boolean) => {
    const label = getMockedLabel({ behaviour });

    expect(isLocal(label)).toBe(expectedResult);
});

it.each([
    // NOTE: Empty labels are considered as global
    [LABEL_BEHAVIOUR.EXCLUSIVE, true],
    [LABEL_BEHAVIOUR.EXCLUSIVE + LABEL_BEHAVIOUR.LOCAL, true],

    [LABEL_BEHAVIOUR.EXCLUSIVE + LABEL_BEHAVIOUR.GLOBAL, true],
    [LABEL_BEHAVIOUR.EXCLUSIVE + LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.GLOBAL, true],
    [LABEL_BEHAVIOUR.LOCAL, false],
    [LABEL_BEHAVIOUR.GLOBAL, true],
    [LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.GLOBAL, true],
])('isGlobal(%o) === %o', (behaviour: LABEL_BEHAVIOUR, expectedResult: boolean) => {
    const label = getMockedLabel({ behaviour });

    expect(isGlobal(label)).toBe(expectedResult);
});

it.each([
    [LABEL_BEHAVIOUR.ANOMALOUS, true],
    [LABEL_BEHAVIOUR.LOCAL, false],
])('isAnomalous(%o) === %o', (behaviour: LABEL_BEHAVIOUR, expectedResult: boolean) => {
    const label = getMockedLabel({ behaviour });

    expect(isAnomalous(label)).toBe(expectedResult);
});

describe('Label behaviour based on task type', () => {
    const labelDTO: LabelDTO = {
        id: '1',
        color: 'red',
        name: 'Hearts',
        group: 'suit',
        hotkey: 'ctrl+1',
        parent_id: null,
        is_empty: false,
        is_background: false,
        is_anomalous: false,
    };

    it.each([DOMAIN.CLASSIFICATION, DOMAIN.DETECTION, DOMAIN.SEGMENTATION])(
        'gives empty labels a GLOBAL and EMPTY behavior for %o domain',
        (domain: DOMAIN) => {
            expect(getBehaviourFromDTO({ ...labelDTO, is_empty: true }, domain)).toEqual(
                LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.EXCLUSIVE
            );
        }
    );

    it('gives labels from classification tasks a GLOBAL behavior', () => {
        expect(getBehaviourFromDTO(labelDTO, DOMAIN.CLASSIFICATION)).toEqual(LABEL_BEHAVIOUR.GLOBAL);
    });

    it('gives labels from detection tasks a LOCAL behavior', () => {
        expect(getBehaviourFromDTO(labelDTO, DOMAIN.DETECTION)).toEqual(LABEL_BEHAVIOUR.LOCAL);
    });

    it('gives labels from segmentation tasks a LOCAL behavior', () => {
        expect(getBehaviourFromDTO(labelDTO, DOMAIN.SEGMENTATION)).toEqual(LABEL_BEHAVIOUR.LOCAL);
    });

    it('gives the normal label an empty behaviour', () => {
        expect(getBehaviourFromDTO({ ...labelDTO, name: 'Normal' }, DOMAIN.ANOMALY_CLASSIFICATION)).toEqual(
            LABEL_BEHAVIOUR.GLOBAL + LABEL_BEHAVIOUR.EXCLUSIVE
        );
    });

    it.each([DOMAIN.ANOMALY_CLASSIFICATION, DOMAIN.ANOMALY_DETECTION, DOMAIN.ANOMALY_SEGMENTATION])(
        'gives anomalous behaviour to anomalous labels for %o domain',
        (domain) => {
            const behaviour = getBehaviourFromDTO({ ...labelDTO, name: 'Anomalous', is_anomalous: true }, domain);
            const label = getMockedLabel({ behaviour });

            expect(isAnomalous(label)).toEqual(true);
        }
    );

    it.each([DOMAIN.CLASSIFICATION, DOMAIN.DETECTION, DOMAIN.SEGMENTATION])(
        'does not give anomalous behaviour to anomalous labels for %o domain',
        (domain) => {
            const behaviour = getBehaviourFromDTO({ ...labelDTO, name: 'Anomalous' }, domain);
            const label = getMockedLabel({ behaviour });

            expect(isAnomalous(label)).not.toEqual(true);
        }
    );
});

describe('Flatten items', () => {
    it('Get flatten labels', () => {
        const flattenLabels = getFlattenedLabels(MOCKED_HIERARCHY);
        expect(flattenLabels.map(({ name }) => name)).toStrictEqual([
            'Cat',
            'Dog',
            'White',
            'Black',
            'Mixed',
            'Hamster',
        ]);
    });

    it('Get flatten groups', () => {
        const flattenGroups = getFlattenedGroups(MOCKED_HIERARCHY);
        expect(flattenGroups.map(({ name }) => name)).toStrictEqual(['Animal', 'Color']);
    });
});

describe('filter empty labels', () => {
    const label = getMockedLabel({ isEmpty: false, name: 'test' });
    const labelTwo = getMockedLabel({ isEmpty: false, name: 'test-2' });
    const emptyLabel = getMockedLabel({ isEmpty: true, name: 'no object' });
    const taskOne = getMockedTask({ labels: [label, emptyLabel] });
    const taskTwo = getMockedTask({ labels: [labelTwo] });

    it('getNonEmptyLabelsFromProject', () => {
        expect(getNonEmptyLabelsFromProject([taskOne, taskTwo])).toEqual([label, labelTwo]);
    });

    it('getNotEmptyLabelsFromOneTask', () => {
        expect(getNotEmptyLabelsFromOneTask(getMockedTask({ labels: [label, emptyLabel] }))).toEqual([label]);
    });

    it('filters the non-empty labels correctly', () => {
        const mockTasks = [
            getMockedTask({
                domain: DOMAIN.CLASSIFICATION,
                labels: [getMockedLabel({ name: 'No class', isEmpty: true }), getMockedLabel({ name: 'Label 1' })],
            }),
            getMockedTask({
                domain: DOMAIN.DETECTION,
                labels: [getMockedLabel({ name: 'No object', isEmpty: true }), getMockedLabel({ name: 'Label 2' })],
            }),
            getMockedTask({
                domain: DOMAIN.SEGMENTATION,
                labels: [getMockedLabel({ name: 'No object', isEmpty: true }), getMockedLabel({ name: 'Label 3' })],
            }),
            getMockedTask({
                domain: DOMAIN.ANOMALY_DETECTION,
                labels: [getMockedLabel({ name: 'Anomalous' }), getMockedLabel({ name: 'Normal' })],
            }),
            getMockedTask({
                domain: DOMAIN.CLASSIFICATION,
                labels: [getMockedLabel({ name: 'Empty', isEmpty: true }), getMockedLabel({ name: 'Label 4' })],
            }),
        ];

        expect(getNonEmptyLabelsFromProject(mockTasks)).toEqual([
            getMockedLabel({ name: 'Label 1' }),
            getMockedLabel({ name: 'Label 2' }),
            getMockedLabel({ name: 'Label 3' }),
            getMockedLabel({ name: 'Anomalous' }),
            getMockedLabel({ name: 'Normal' }),
            getMockedLabel({ name: 'Label 4' }),
        ]);
    });
});

const getLabel = (name: string, id: string, exclusive = false): Label => {
    return getMockedLabel({
        name,
        id,
        parentLabelId: null,
        isExclusive: exclusive,
    });
};

describe('filter out exclusive labels', () => {
    it('there is one exclusive label and two not empty - should leave two of them', () => {
        const labels: Label[] = [
            getLabel('Exclusive Detection task label', '1', true),
            getLabel('cat', '2'),
            getLabel('dog', '3'),
        ];

        expect(filterOutExclusiveLabel(labels)).toHaveLength(2);
    });

    it('there is two exclusive labels and one not empty - should leave one', () => {
        const labels: Label[] = [
            getLabel('Exclusive Detection task label', '1', true),
            getLabel('Exclusive Segmentation task label', '2', true),
            getLabel('dog', '3'),
        ];

        expect(filterOutExclusiveLabel(labels)).toHaveLength(1);
    });

    it('there is 6 labels and exclusive is in a middle - should leave 5', () => {
        const labels: Label[] = [
            getLabel('hamster', '1'),
            getLabel('bird', '2'),
            getLabel('dog', '3'),
            getLabel('mouse', '4'),
            getLabel('Exclusive Detection task label', '5', true),
            getLabel('cat', '6'),
        ];

        expect(filterOutExclusiveLabel(labels)).toHaveLength(5);
    });

    it('there is one not exclusive label - should leave one', () => {
        const labels: Label[] = [getLabel('dog', '1')];

        expect(filterOutExclusiveLabel(labels)).toHaveLength(1);
    });

    it('there is one exclusive label - should leave none', () => {
        const labels: Label[] = [getLabel('Exclusive Segmentation task label', '1', true)];

        expect(filterOutExclusiveLabel(labels)).toHaveLength(0);
    });

    it('there is no labels - should return exclusive array', () => {
        const labels: Label[] = [];

        expect(filterOutExclusiveLabel(labels)).toHaveLength(0);
    });
});
