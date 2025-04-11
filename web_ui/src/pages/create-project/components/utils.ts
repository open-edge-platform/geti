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

import * as yup from 'yup';

import { LabelItemType, LabelTreeItem, LabelTreeLabelProps } from '../../../core/labels/label-tree-view.interface';
import { trimAndLowerCase, trimText } from '../../../shared/utils';
import { ProjectMetadata, STEPS } from '../new-project-dialog-provider/new-project-dialog-provider.interface';

const labelNameNotAllowedMultipleSpaces = new RegExp(/^((?! {2}).)*$/);

export const REQUIRED_NAME_VALIDATION_MESSAGE = 'Name cannot be empty';
export const ONE_SPACE_VALIDATION_MESSAGE = 'You can only use a single space';
export const UNIQUE_LABEL_HOTKEY_VALIDATION_MESSAGE = 'This hotkey is already being used';
const UNIQUE_ANNOTATOR_HOTKEY_VALIDATION_MESSAGE = 'This hotkey is reserved for operations on annotator page';
export const REQUIRED_PROJECT_NAME_VALIDATION_MESSAGE = 'Project name cannot be empty';
export const MORE_THAT_ONE_HUNDRED_VALIDATION_MESSAGE = 'Name cannot have more than 100 characters';

export const UNIQUE_VALIDATION_MESSAGE = (name: string, type: LabelItemType): string =>
    `${type === LabelItemType.LABEL ? 'Label' : 'Group'} '${name}' already exists`;

export const MAX_NUMBER_OF_CHARACTERS_OF_PROJECT_NAME = 100;

const returnLabelItems = (items: LabelTreeItem[]): LabelTreeLabelProps[] =>
    items.filter(({ type }) => type === LabelItemType.LABEL) as LabelTreeLabelProps[];

const isUniqueInProjectLabels =
    (projectLabels: LabelTreeLabelProps[], property: 'name' | 'hotkey', currentItemId: string | undefined) =>
    (name?: string): boolean => {
        if (!name && property === 'hotkey') {
            return true;
        }

        return (
            name !== undefined &&
            !projectLabels.some(
                (item) =>
                    item.id !== currentItemId && trimAndLowerCase(item[property] as string) === trimAndLowerCase(name)
            )
        );
    };

const isUniqueNameInProjectItems =
    (items: LabelTreeItem[], currentItemId?: string) =>
    (name?: string): boolean => {
        const otherItems = items.filter((item) => item.id !== currentItemId);
        return !name || (!!name && !otherItems.some((item) => trimAndLowerCase(item.name) === trimAndLowerCase(name)));
    };

const MAX_NUMBER_OF_VISIBLE_CHARACTERS = 40;

export const newLabelNameSchema = (
    name: string | undefined,
    currentItemId: string | undefined,
    projectLabels: LabelTreeItem[],
    itemType: LabelItemType
): yup.Schema<{ name: string }> => {
    return yup.object({
        name: yup
            .string()
            .trim()
            .required(REQUIRED_NAME_VALIDATION_MESSAGE)
            .max(100, MORE_THAT_ONE_HUNDRED_VALIDATION_MESSAGE)
            .test(
                'unique',
                UNIQUE_VALIDATION_MESSAGE(
                    name ? trimText(name.trim(), MAX_NUMBER_OF_VISIBLE_CHARACTERS) : '',
                    itemType
                ),
                isUniqueNameInProjectItems(projectLabels, currentItemId)
            )
            .matches(labelNameNotAllowedMultipleSpaces, ONE_SPACE_VALIDATION_MESSAGE),
    });
};

export const newLabelHotkeySchema = (
    currentItemId: string | undefined,
    projectLabels: LabelTreeItem[],
    annotatorHotkeys: string[]
): yup.Schema<{ hotkey?: string | undefined }> =>
    yup.object({
        hotkey: yup
            .string()
            .test('unique-in-annotator', UNIQUE_ANNOTATOR_HOTKEY_VALIDATION_MESSAGE, (hotkey) => {
                if (hotkey === undefined) return false;

                return !annotatorHotkeys.some((annotatorHotkey) =>
                    // The split here takes care of the cases where we have multiple hotkeys for the same action
                    // e.g. "ctrl+c, cmd+c"
                    annotatorHotkey.split(',').includes(hotkey.toLocaleLowerCase())
                );
            })
            .test(
                'unique-in-labels',
                UNIQUE_LABEL_HOTKEY_VALIDATION_MESSAGE,
                isUniqueInProjectLabels(returnLabelItems(projectLabels), 'hotkey', currentItemId)
            ),
    });

export const projectNameSchema = (): yup.Schema<{ name: string }> =>
    yup.object({
        name: yup.string().trim().required(REQUIRED_PROJECT_NAME_VALIDATION_MESSAGE),
    });

export enum ProjectNameErrorPath {
    NAME = 'name',
}

export const getStepInfo = (step: STEPS) => {
    switch (step) {
        case STEPS.NAME_PROJECT:
            return { title: 'Type project name', number: 1 };
        case STEPS.SELECT_TEMPLATE:
            return { title: 'Select task type', number: 2 };
        case STEPS.POSE_TEMPLATE:
            return { title: 'Create template', number: 3 };
        case STEPS.LABEL_MANAGEMENT_SECOND_TASK:
            return { title: 'Create labels', number: 4 };
        default:
            return { title: 'Create labels', number: 3 };
    }
};

export const getTotalSteps = ({ currentStep, selectedTab }: ProjectMetadata) => {
    if (currentStep === STEPS.SELECT_TEMPLATE && selectedTab === 'Anomaly') {
        return 2;
    }

    if (selectedTab === 'Chained tasks') {
        return 4;
    }

    return 3;
};
