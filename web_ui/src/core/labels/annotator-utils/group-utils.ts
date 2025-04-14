// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
