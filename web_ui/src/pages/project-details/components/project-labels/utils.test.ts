// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    LabelItemEditionState,
    LabelItemType,
    LabelTreeLabelProps,
} from '../../../../core/labels/label-tree-view.interface';
import { LabelsRelationType } from '../../../../core/labels/label.interface';
import { GROUP_SEPARATOR } from '../../../../core/labels/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { getMockedLabel, getMockedTreeLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getLabelsWithState, getRelation } from './utils';

describe('Project labels utils', () => {
    describe('getLabelsWithState', () => {
        it('return labels which are new', () => {
            const labels = [
                getMockedTreeLabel({ state: LabelItemEditionState.NEW, type: LabelItemType.LABEL }),
                getMockedTreeLabel({
                    state: LabelItemEditionState.IDLE,
                    type: LabelItemType.LABEL,
                }),
                getMockedTreeLabel({ state: LabelItemEditionState.NEW, type: LabelItemType.LABEL }),
            ];

            const returnedLabels = getLabelsWithState(labels as LabelTreeLabelProps[], [LabelItemEditionState.NEW]);
            expect(returnedLabels).toHaveLength(2);
        });

        it('return labels which are idle or removed', () => {
            const labels = [
                getMockedTreeLabel({ state: LabelItemEditionState.NEW, type: LabelItemType.LABEL }),
                getMockedTreeLabel({
                    state: LabelItemEditionState.IDLE,
                    type: LabelItemType.LABEL,
                }),
                getMockedTreeLabel({ state: LabelItemEditionState.NEW, type: LabelItemType.LABEL }),
                getMockedTreeLabel({ state: LabelItemEditionState.REMOVED, type: LabelItemType.LABEL }),
                getMockedTreeLabel({ state: LabelItemEditionState.REMOVED, type: LabelItemType.LABEL }),
            ];

            const returnedLabels = getLabelsWithState(labels as LabelTreeLabelProps[], [
                LabelItemEditionState.IDLE,
                LabelItemEditionState.REMOVED,
            ]);
            expect(returnedLabels).toHaveLength(3);
        });

        it('getLabelsWithState with no state', () => {
            const labels = [
                getMockedTreeLabel({ state: LabelItemEditionState.NEW, type: LabelItemType.LABEL }),
                getMockedTreeLabel({
                    state: LabelItemEditionState.IDLE,
                    type: LabelItemType.LABEL,
                }),
                getMockedTreeLabel({ state: LabelItemEditionState.NEW, type: LabelItemType.LABEL }),
                getMockedTreeLabel({ state: LabelItemEditionState.REMOVED, type: LabelItemType.LABEL }),
                getMockedTreeLabel({ state: LabelItemEditionState.REMOVED, type: LabelItemType.LABEL }),
            ];

            const returnedLabels = getLabelsWithState(labels as LabelTreeLabelProps[], []);
            expect(returnedLabels).toHaveLength(0);
        });
    });
});

describe('getRelation function', () => {
    it('Project is task chain - MIXED', () => {
        expect(getRelation([], [DOMAIN.DETECTION, DOMAIN.CLASSIFICATION])).toBe(LabelsRelationType.MIXED);
    });

    it('Project is Detection - SINGLE SELECTION', () => {
        expect(getRelation([], [DOMAIN.DETECTION])).toBe(LabelsRelationType.SINGLE_SELECTION);
    });

    it('Project is Segmentation - SINGLE SELECTION', () => {
        expect(getRelation([], [DOMAIN.SEGMENTATION])).toBe(LabelsRelationType.SINGLE_SELECTION);
    });

    /* There is no way to know which project user created
     all of the classification projects will have mixed mode in label tab */
    it('Project is Classification - all labels in the same group - MIXED', () => {
        expect(
            getRelation(
                [
                    getMockedLabel({ name: 'test1', group: 'Default' }),
                    getMockedLabel({ name: 'test2', group: 'Default' }),
                    getMockedLabel({ name: 'test3', group: 'Default' }),
                ],
                [DOMAIN.CLASSIFICATION]
            )
        ).toBe(LabelsRelationType.MIXED);
    });

    it('Project is Classification - all labels in different group - MIXED', () => {
        expect(
            getRelation(
                [
                    getMockedLabel({ name: 'test1', group: 'test1' }),
                    getMockedLabel({ name: 'test2', group: 'test2' }),
                    getMockedLabel({ name: 'test3', group: 'test3' }),
                ],
                [DOMAIN.CLASSIFICATION]
            )
        ).toBe(LabelsRelationType.MIXED);
    });

    it('Project is Classification - some in the same group some in different - MIXED', () => {
        expect(
            getRelation(
                [
                    getMockedLabel({ name: 'test1', group: 'root' }),
                    getMockedLabel({ name: 'test2', group: 'root' }),
                    getMockedLabel({ name: 'test3', group: 'root_test' }),
                    getMockedLabel({ name: 'test4', group: 'root_test' }),
                    getMockedLabel({ name: 'test5', group: 'root_test_subgroup' }),
                ],
                [DOMAIN.CLASSIFICATION]
            )
        ).toBe(LabelsRelationType.MIXED);
    });

    it('Project is Classification - there is group hierarchy and only one label in group - MIXED', () => {
        expect(
            getRelation(
                [
                    getMockedLabel({ name: '11', group: '1', id: '1' }),
                    getMockedLabel({ name: '1111', group: `1${GROUP_SEPARATOR}111`, parentLabelId: '1' }),
                    getMockedLabel({ name: '22', group: '2', id: '2' }),
                    getMockedLabel({ name: '2222', group: `2${GROUP_SEPARATOR}222`, parentLabelId: '2' }),
                    getMockedLabel({ name: '33', group: '3', id: '3' }),
                    getMockedLabel({ name: '3333', group: `3${GROUP_SEPARATOR}333`, parentLabelId: '3' }),
                ],
                [DOMAIN.CLASSIFICATION]
            )
        ).toBe(LabelsRelationType.MIXED);
    });
});
