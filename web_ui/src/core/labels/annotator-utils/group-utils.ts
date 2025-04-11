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

import uniq from 'lodash/uniq';

import { LabelTreeLabelProps } from '../label-tree-view.interface';
import { Label, LabelsRelationType } from '../label.interface';
import { GROUP_SEPARATOR } from '../utils';

export const separateGroup = (groupName: string | null): string[] =>
    groupName ? groupName.split(GROUP_SEPARATOR) : [];

export const getLowestLevelGroupName = (groupName: string): string => {
    const separatedGroups = separateGroup(groupName);

    return separatedGroups[separatedGroups.length - 1];
};

export const getGroupWithoutLowestLevel = (groupName: string): string => {
    const separatedGroups = separateGroup(groupName);
    const baseGroupName = separatedGroups.slice(0, -1);
    return baseGroupName.join(GROUP_SEPARATOR);
};

export const getEditedMultiLabelGroupName = (
    editedLabel: LabelTreeLabelProps,
    previousRelation: LabelsRelationType,
    isNew: boolean
): string => {
    let newGroupName = editedLabel.group;
    if (previousRelation === LabelsRelationType.MULTI_SELECTION && isNew) {
        newGroupName = getGroupWithoutLowestLevel(editedLabel.group);
    }

    if (editedLabel.relation === LabelsRelationType.MULTI_SELECTION && isNew) {
        newGroupName = getFullGroupName(newGroupName, editedLabel.name);
    }

    return newGroupName;
};

export const getGroupRelation = (
    allLabels: ReadonlyArray<Label>,
    groupName: string,
    groupParentId: string | null
): LabelsRelationType => {
    const descendants = allLabels.filter((label) => {
        return isGroupChild(label, groupName, groupParentId);
    });
    const uniqueDescendantsGroupNames = uniq(descendants.map(({ group }) => group));

    return uniqueDescendantsGroupNames.length > 1 && !uniqueDescendantsGroupNames.some((group) => groupName === group)
        ? LabelsRelationType.MULTI_SELECTION
        : LabelsRelationType.SINGLE_SELECTION;
};

export const getFullGroupName = (parentGroup: string | null, group: string): string => {
    return parentGroup ? `${parentGroup}${GROUP_SEPARATOR}${group}` : group;
};

const isDescendant = (group: string, parentGroup: string): boolean => {
    return group.startsWith(`${parentGroup}${GROUP_SEPARATOR}`);
};

const isGroupChild = (label: Label, groupName: string, groupParentId: string | null): boolean => {
    return isDescendant(label.group, groupName) && groupParentId === label.parentLabelId;
};
