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

import { LabelItemType, LabelTreeItem } from '../../../core/labels/label-tree-view.interface';
import { LabelsRelationType } from '../../../core/labels/label.interface';
import { DOMAIN } from '../../../core/projects/core.interface';
import { getMockedTreeLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { MORE_THAN_100_CHARS_NAME } from '../../../test-utils/utils';
import {
    CreateNewProjectSelectedTabType,
    ProjectMetadata,
    ProjectType,
    STEPS,
} from '../new-project-dialog-provider/new-project-dialog-provider.interface';
import {
    getStepInfo,
    getTotalSteps,
    MORE_THAT_ONE_HUNDRED_VALIDATION_MESSAGE,
    newLabelNameSchema,
    ONE_SPACE_VALIDATION_MESSAGE,
    projectNameSchema,
    REQUIRED_NAME_VALIDATION_MESSAGE,
    REQUIRED_PROJECT_NAME_VALIDATION_MESSAGE,
    UNIQUE_VALIDATION_MESSAGE,
} from './utils';

const emptyLabels: LabelTreeItem[] = [];

describe('label name validation', () => {
    it('name should be unique', () => {
        const labelName = 'test';
        const labels = [getMockedTreeLabel({ name: 'test' })];

        expect(() =>
            newLabelNameSchema(labelName, undefined, labels, LabelItemType.LABEL).validateSync({ name: labelName })
        ).toThrow(UNIQUE_VALIDATION_MESSAGE('test', LabelItemType.LABEL));
    });

    it('empty name should throw an error', () => {
        const emptyName = '';

        expect(() =>
            newLabelNameSchema(emptyName, undefined, emptyLabels, LabelItemType.LABEL).validateSync({ name: emptyName })
        ).toThrow(REQUIRED_NAME_VALIDATION_MESSAGE);
    });

    it('white spaces should throw an error', () => {
        const labelName = ' ';

        expect(() =>
            newLabelNameSchema(labelName, undefined, emptyLabels, LabelItemType.LABEL).validateSync({ name: labelName })
        ).toThrow(REQUIRED_NAME_VALIDATION_MESSAGE);
    });

    it('name with Leading space show throw an error', () => {
        const name = 'test';
        const labelName = ` ${name}`;
        const labels = [getMockedTreeLabel({ name })];

        expect(() =>
            newLabelNameSchema(labelName, undefined, labels, LabelItemType.LABEL).validateSync({ name: labelName })
        ).toThrow(UNIQUE_VALIDATION_MESSAGE(name, LabelItemType.LABEL));
    });

    it('name with trailing spaces show throw an error', () => {
        const name = 'test';
        const labelName = `${name} `;
        const labels = [getMockedTreeLabel({ name })];

        expect(() =>
            newLabelNameSchema(labelName, undefined, labels, LabelItemType.LABEL).validateSync({ name: labelName })
        ).toThrow(UNIQUE_VALIDATION_MESSAGE(name, LabelItemType.LABEL));
    });

    it('previously saved names with trailing spaces are trim and validate', () => {
        const name = 'test';
        const labels = [getMockedTreeLabel({ name: `${name} ` })];

        expect(() => newLabelNameSchema(name, undefined, labels, LabelItemType.LABEL).validateSync({ name })).toThrow(
            UNIQUE_VALIDATION_MESSAGE(name, LabelItemType.LABEL)
        );
    });

    it('name with more than 100 character throw an error', () => {
        const labelName = MORE_THAN_100_CHARS_NAME;

        expect(() =>
            newLabelNameSchema(labelName, undefined, emptyLabels, LabelItemType.LABEL).validateSync({ name: labelName })
        ).toThrow(MORE_THAT_ONE_HUNDRED_VALIDATION_MESSAGE);
    });

    it('name containing two spaces in row are not permitted', () => {
        const labelName = 'label  name';

        expect(() =>
            newLabelNameSchema(labelName, undefined, emptyLabels, LabelItemType.LABEL).validateSync({ name: labelName })
        ).toThrow(ONE_SPACE_VALIDATION_MESSAGE);
    });
});

describe('project name validation', () => {
    it('empty name should throw an error', () => {
        const emptyName = '';
        expect(() => projectNameSchema().validateSync({ name: emptyName })).toThrow(
            REQUIRED_PROJECT_NAME_VALIDATION_MESSAGE
        );
    });

    it('white spaces should throw an error', () => {
        const emptyName = ' ';

        expect(() => projectNameSchema().validateSync({ name: emptyName })).toThrow(
            REQUIRED_PROJECT_NAME_VALIDATION_MESSAGE
        );
    });
});

describe('getStepInfo', () => {
    test.each([
        [STEPS.NAME_PROJECT, { title: 'Type project name', number: 1 }],
        [STEPS.SELECT_TEMPLATE, { title: 'Select task type', number: 2 }],
        [STEPS.POSE_TEMPLATE, { title: 'Create template', number: 3 }],
        [STEPS.LABEL_MANAGEMENT_SECOND_TASK, { title: 'Create labels', number: 4 }],
        ['UNKNOWN_STEP' as STEPS, { title: 'Create labels', number: 3 }],
    ])('returns the step info for %s', (step, expected) => {
        expect(getStepInfo(step)).toEqual(expected);
    });
});

describe('getTotalSteps', () => {
    const getMockedProjectMetadata = (props: Partial<ProjectMetadata>): ProjectMetadata => {
        return {
            name: 'test',
            selectedDomains: [DOMAIN.SEGMENTATION],
            projectTypeMetadata: [
                { domain: DOMAIN.SEGMENTATION, labels: [], relation: LabelsRelationType.SINGLE_SELECTION },
            ],
            selectedTab: 'Detection',
            currentStep: STEPS.SELECT_TEMPLATE,
            projectType: ProjectType.SINGLE,
            ...props,
        };
    };
    test.each([
        ['Anomaly' as CreateNewProjectSelectedTabType, STEPS.SELECT_TEMPLATE, 2],
        ['Chained tasks' as CreateNewProjectSelectedTabType, STEPS.NAME_PROJECT, 4],
        ['Detection' as CreateNewProjectSelectedTabType, STEPS.NAME_PROJECT, 3],
    ])('returns total steps for %s selected tab', (selectedTab, currentStep, expectedSteps) => {
        expect(getTotalSteps(getMockedProjectMetadata({ currentStep, selectedTab }))).toBe(expectedSteps);
    });
});
