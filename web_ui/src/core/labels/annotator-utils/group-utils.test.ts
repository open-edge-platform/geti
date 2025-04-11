// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { getMockedLabel, getMockedTreeLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { Label, LabelsRelationType } from '../label.interface';
import { GROUP_SEPARATOR } from '../utils';
import {
    getEditedMultiLabelGroupName,
    getFullGroupName,
    getGroupRelation,
    getGroupWithoutLowestLevel,
    getLowestLevelGroupName,
    separateGroup,
} from './group-utils';

describe('Group utils', () => {
    const SINGLE_LEVEL_GROUP = 'Group 1';
    const MULTI_LEVEL_GROUP = 'Group 1___Label 1___test___1.1.1';

    describe('Group utils - getGroupRelation', () => {
        describe('getGroupRelation - flat structure', () => {
            const labels: ReadonlyArray<Label> = [
                getMockedLabel({ name: 'label1', group: 'group___child1' }),
                getMockedLabel({ name: 'label3', group: 'group1' }),
                getMockedLabel({ name: 'label4', group: 'group1' }),
                getMockedLabel({ name: 'label2', group: 'group___child2' }),
            ];

            it('Check if labels with groups: group>child, group1 return multi selection in group', () => {
                expect(getGroupRelation(labels, 'group', null)).toBe(LabelsRelationType.MULTI_SELECTION);
            });
            it('Check if labels with groups: group>child, group1 return single selection in group1', () => {
                expect(getGroupRelation(labels, 'group1', null)).toBe(LabelsRelationType.SINGLE_SELECTION);
            });
        });

        describe('getGroupRelation - hierarchy', () => {
            const labels: ReadonlyArray<Label> = [
                getMockedLabel({ name: 'b', group: 'a', id: 'label_b', parentLabelId: null }),
                getMockedLabel({ name: 'bba', group: 'a___bb', parentLabelId: 'label_b', id: 'label_bba' }),
                getMockedLabel({ name: 'bbb', group: 'a___bb', parentLabelId: 'label_b', id: 'label_bbb' }),
                getMockedLabel({ name: 'c', group: 'a', parentLabelId: null }),
            ];

            it('Check if group a will be Single selection', () => {
                expect(getGroupRelation(labels, 'a', null)).toBe(LabelsRelationType.SINGLE_SELECTION);
            });
        });
    });

    describe('Group utils - separateGroup', () => {
        it('Check separating groups for empty group case', () => {
            expect(separateGroup(null)).toStrictEqual([]);
        });

        it('Check separating groups for single group', () => {
            expect(separateGroup(SINGLE_LEVEL_GROUP)).toStrictEqual(['Group 1']);
        });

        it('Check separating groups for multi level groups', () => {
            expect(separateGroup(MULTI_LEVEL_GROUP)).toStrictEqual(['Group 1', 'Label 1', 'test', '1.1.1']);
        });
    });

    describe('Group utils - getLowestLevelGroupName', () => {
        it('Get lower level group of single group', () => {
            expect(getLowestLevelGroupName(SINGLE_LEVEL_GROUP)).toBe('Group 1');
        });

        it('Get lower level group of multi level group', () => {
            expect(getLowestLevelGroupName(MULTI_LEVEL_GROUP)).toBe('1.1.1');
        });
    });

    describe('Group utils - getGroupWithoutLowestLevel', () => {
        it('Group without lowest level single group', () => {
            expect(getGroupWithoutLowestLevel(SINGLE_LEVEL_GROUP)).toBe('');
        });

        it('Group without lowest level multi level group', () => {
            expect(getGroupWithoutLowestLevel(MULTI_LEVEL_GROUP)).toBe('Group 1___Label 1___test');
        });
    });

    describe('Group utils - getEditedMultiLabelGroupName', () => {
        it('getEditedMultiLabelGroupName - not edited multi selection relation ', () => {
            expect(
                getEditedMultiLabelGroupName(
                    getMockedTreeLabel({
                        name: 'new name',
                        group: 'Group___old name',
                        relation: LabelsRelationType.MULTI_SELECTION,
                    }),
                    LabelsRelationType.MULTI_SELECTION,
                    true
                )
            ).toBe('Group___new name');
        });

        it('getEditedMultiLabelGroupName - single selection to multi selection relation ', () => {
            expect(
                getEditedMultiLabelGroupName(
                    getMockedTreeLabel({
                        name: 'new name',
                        group: 'Group',
                        relation: LabelsRelationType.MULTI_SELECTION,
                    }),
                    LabelsRelationType.SINGLE_SELECTION,
                    true
                )
            ).toBe('Group___new name');
        });

        it('getEditedMultiLabelGroupName - not edited single selection relation ', () => {
            expect(
                getEditedMultiLabelGroupName(
                    getMockedTreeLabel({
                        name: 'new name',
                        group: 'Group',
                        relation: LabelsRelationType.SINGLE_SELECTION,
                    }),
                    LabelsRelationType.SINGLE_SELECTION,
                    true
                )
            ).toBe('Group');
        });

        it('getEditedMultiLabelGroupName - multi selection to single selection relation ', () => {
            expect(
                getEditedMultiLabelGroupName(
                    getMockedTreeLabel({
                        name: 'new name',
                        group: 'Group___old name',
                        relation: LabelsRelationType.SINGLE_SELECTION,
                    }),
                    LabelsRelationType.MULTI_SELECTION,
                    true
                )
            ).toBe('Group');
        });
    });

    describe('Group utils - getFullGroupName', () => {
        it('getFullGroupName - Empty parent group', () => {
            expect(getFullGroupName(null, SINGLE_LEVEL_GROUP)).toBe(SINGLE_LEVEL_GROUP);
        });

        it('getFullGroupName - single level parent group', () => {
            expect(getFullGroupName(SINGLE_LEVEL_GROUP, SINGLE_LEVEL_GROUP)).toBe(
                `${SINGLE_LEVEL_GROUP}${GROUP_SEPARATOR}${SINGLE_LEVEL_GROUP}`
            );
        });

        it('getFullGroupName - multi level parent group', () => {
            expect(getFullGroupName(MULTI_LEVEL_GROUP, SINGLE_LEVEL_GROUP)).toBe(
                `${MULTI_LEVEL_GROUP}${GROUP_SEPARATOR}${SINGLE_LEVEL_GROUP}`
            );
        });
    });
});
