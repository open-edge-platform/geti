// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { LabelTreeItem } from '../../../../core/labels/label-tree-view.interface';
import { LabelsRelationType } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { TaskMetadata } from '../../../../core/projects/task.interface';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { LABEL_TREE_TYPE } from './label-tree-type.enum';
import { getLabelTreeType, getProjectLabels } from './utils';

describe('Get label tree type', () => {
    it('DETECTION domain should give FLAT tree type', () => {
        expect(getLabelTreeType(DOMAIN.DETECTION, false)).toBe(LABEL_TREE_TYPE.FLAT);
    });

    it('DETECTION domain from DOMAIN > CLASSIFICATION should give SINGLE tree type', () => {
        expect(getLabelTreeType(DOMAIN.DETECTION, true)).toBe(LABEL_TREE_TYPE.SINGLE);
    });

    it('CLASSIFICATION domain should give HIERARCHY tree type', () => {
        expect(getLabelTreeType(DOMAIN.CLASSIFICATION, false)).toBe(LABEL_TREE_TYPE.HIERARCHY);
    });

    it('CLASSIFICATION domain from CLASSIFICATION > CROP should give HIERARCHY tree type', () => {
        expect(getLabelTreeType(DOMAIN.CLASSIFICATION, true)).toBe(LABEL_TREE_TYPE.SINGLE);
    });
});

describe('Get labels names from all of the tasks from project', () => {
    it('Get labels names from project with no tasks', () => {
        const tasksLabels: TaskMetadata[] = [];
        expect(getProjectLabels(tasksLabels)).toStrictEqual([]);
    });

    it('Get labels names from project when there is one task with no labels', () => {
        const tasksLabels: TaskMetadata[] = [
            {
                labels: [],
                domain: DOMAIN.SEGMENTATION,
                relation: LabelsRelationType.SINGLE_SELECTION,
            },
        ];
        expect(getProjectLabels(tasksLabels)).toStrictEqual([]);
    });

    it('Get labels names from project when there is one task with couple of labels', () => {
        const tasksLabels: TaskMetadata[] = [
            {
                labels: [
                    getMockedLabel({ name: 'test label' }),
                    getMockedLabel({ name: 'test label 2' }),
                    getMockedLabel({ name: 'test label 3' }),
                ] as LabelTreeItem[],
                domain: DOMAIN.SEGMENTATION,
                relation: LabelsRelationType.SINGLE_SELECTION,
            },
        ];
        expect(getProjectLabels(tasksLabels)).toStrictEqual([
            getMockedLabel({ name: 'test label' }),
            getMockedLabel({ name: 'test label 2' }),
            getMockedLabel({ name: 'test label 3' }),
        ]);
    });

    it('Get labels names from project when there are two tasks with couple of labels', () => {
        const tasksLabels: TaskMetadata[] = [
            {
                labels: [getMockedLabel({ name: 'detection label' })] as LabelTreeItem[],
                domain: DOMAIN.DETECTION,
                relation: LabelsRelationType.SINGLE_SELECTION,
            },
            {
                labels: [
                    getMockedLabel({ name: 'test label' }),
                    getMockedLabel({ name: 'test label 2' }),
                    getMockedLabel({ name: 'test label 3' }),
                ] as LabelTreeItem[],
                domain: DOMAIN.SEGMENTATION,
                relation: LabelsRelationType.SINGLE_SELECTION,
            },
        ];
        expect(getProjectLabels(tasksLabels)).toStrictEqual([
            getMockedLabel({ name: 'detection label' }),
            getMockedLabel({ name: 'test label' }),
            getMockedLabel({ name: 'test label 2' }),
            getMockedLabel({ name: 'test label 3' }),
        ]);
    });
});
