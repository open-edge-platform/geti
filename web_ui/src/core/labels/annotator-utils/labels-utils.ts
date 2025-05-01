// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { hasEqualId, hasEqualSize } from '@shared/utils';
import groupBy from 'lodash/groupBy';
import isEqual from 'lodash/isEqual';
import isString from 'lodash/isString';
import uniq from 'lodash/uniq';
import uniqBy from 'lodash/uniqBy';

import { idMatchingFormat } from '../../../test-utils/id-utils';
import {
    LabelItemEditionState,
    LabelItemType,
    LabelTreeGroupProps,
    LabelTreeItem,
    LabelTreeLabelProps,
} from '../label-tree-view.interface';
import { Label, LabelsRelationType } from '../label.interface';
import { GROUP_SEPARATOR } from '../utils';
import { getGroupRelation, getLowestLevelGroupName, separateGroup } from './group-utils';

export const findLabelParents = (labels: ReadonlyArray<Label>, item: Label): Label[] => {
    const parents: Label[] = [];
    const parent = labels.find((label: Label) => label.id === item.parentLabelId);

    if (parent) {
        return [parent, ...findLabelParents(labels, parent)];
    }

    return parents;
};

const fetchLabelsChildren = (
    labels: ReadonlyArray<Label>,
    labelId: string | null = null,
    opened: string[] | 'all' = [],
    relation: LabelsRelationType,
    labelsByParentLabelId: Record<string, ReadonlyArray<Label>>
): LabelTreeLabelProps[] => {
    const childLabels = labelsByParentLabelId[labelId ?? 'null'] ?? [];

    return childLabels.map((label: Label): LabelTreeLabelProps => {
        const currentChildren = fetchLabelsChildren(labels, label.id, opened, relation, labelsByParentLabelId);

        return {
            ...label,
            open: opened === 'all' || opened.includes(label.id),
            children: currentChildren,
            inEditMode: false,
            type: LabelItemType.LABEL,
            state: LabelItemEditionState.IDLE,
            relation,
        };
    });
};

export const fetchLabelsTree = (labels: ReadonlyArray<Label>, opened: string[] | 'all' = []): LabelTreeLabelProps[] => {
    // Find all labels that either have no parent, or whose parent is not known
    // because they may not be part of the currently selected task
    const labelRoots = labels.filter((label: Readonly<Label>): boolean => {
        if (label.parentLabelId === null) {
            return true;
        }

        return !labels.some(hasEqualId(label.parentLabelId));
    });

    // Relation does not have impact on this labels tree so set to basic one
    const currentRelation = LabelsRelationType.SINGLE_SELECTION;

    return labelRoots.map((label: Label): LabelTreeLabelProps => {
        const labelsByParentLabelId = groupBy(labels, ({ parentLabelId }: Label) => {
            return parentLabelId ?? 'null';
        });
        const currentChildren = fetchLabelsChildren(labels, label.id, opened, currentRelation, labelsByParentLabelId);

        return {
            ...label,
            open: opened === 'all' || opened.includes(label.id),
            children: currentChildren,
            inEditMode: false,
            type: LabelItemType.LABEL,
            state: LabelItemEditionState.IDLE,
            relation: currentRelation,
        };
    });
};

export const uniqueLabels = (allLabels: Label[]): Label[] => {
    return uniqBy(allLabels, (label: Label) => label.id);
};

const getLabelsByGroup = (labels: ReadonlyArray<Label>, groupName: string, parentId: string | null): Label[] => {
    return labels.filter(({ group, parentLabelId }) => group === groupName && parentLabelId === parentId);
};

const getGroupChildrenGroups = (
    childrenNames: string[],
    allLabels: ReadonlyArray<Label>,
    opened: string[] | 'all' = [],
    parentLabelId: string | null,
    parentGroup: { name: string; relation: LabelsRelationType } | null,
    level: number
): LabelTreeItem[] => {
    return childrenNames.map((group) => {
        const relation = getGroupRelation(allLabels, group, parentLabelId);
        const currentChildren: LabelTreeItem[] = getChildItemsOfGroup(
            group,
            allLabels,
            level,
            opened,
            parentLabelId,
            relation
        );

        if (currentChildren.length === 1 && parentGroup?.relation === LabelsRelationType.MULTI_SELECTION) {
            return currentChildren[0] as LabelTreeLabelProps;
        }

        return {
            id: idMatchingFormat(group),
            name: separateGroup(group)[separateGroup(group).length - 1],
            type: LabelItemType.GROUP,
            parentLabelId: group,
            parentName: parentGroup?.name,
            open: true,
            relation,
            children: currentChildren,
            inEditMode: false,
            state: LabelItemEditionState.IDLE,
        } as LabelTreeGroupProps;
    });
};

const getGroupChildrenLabels = (
    groupLabels: Label[],
    allLabels: ReadonlyArray<Label>,
    opened: string[] | 'all' = [],
    level: number,
    relation: LabelsRelationType
) => {
    return groupLabels.map((label: Label): LabelTreeItem => {
        const currentChildren = fetchLabelsTreeWithGroups(allLabels, opened, label.id, label.group, level + 1);

        return {
            ...label,
            open: opened === 'all' || opened.includes(label.id),
            children: currentChildren,
            inEditMode: false,
            type: LabelItemType.LABEL,
            state: LabelItemEditionState.IDLE,
            relation,
        };
    });
};

const getUniqueChildGroupsNames = (
    labels: ReadonlyArray<Label>,
    groupName: string,
    parentId: string | null
): string[] => {
    const groupHierarchy = separateGroup(groupName);

    const isGroupChildren = ({ group, parentLabelId }: Label) => {
        const currentGroupHierarchy = separateGroup(group);

        if (hasEqualSize(groupHierarchy, currentGroupHierarchy) || parentLabelId !== parentId) {
            return false;
        }

        const parentGroupHierarchy = currentGroupHierarchy.slice(0, currentGroupHierarchy.length - 1);

        return isEqual(groupHierarchy, parentGroupHierarchy);
    };

    return uniq(labels.filter(isGroupChildren).map(({ group }) => group));
};

/* 
    This function return labels hierarchy (with groups representation) from flat labels got from server
*/
export const fetchLabelsTreeWithGroups = (
    labels: ReadonlyArray<Label>,
    opened: string[] | 'all' = [],
    parentId: string | null,
    parentGroup: string | null,
    level = 1
): LabelTreeItem[] => {
    // Find all labels that either have no parent, or whose parent is not known
    // because they may not be part of the currently selected task
    const labelRoots = labels.filter((label: Readonly<Label>): boolean => {
        if (parentId === null) {
            return !labels.some(hasEqualId(label.parentLabelId));
        }

        return label.parentLabelId === parentId;
    });

    /**
     * Take groups of the current level from the list of all existing groups
     * or take groups which are higher level
     */
    const descendantGroups = labelRoots
        .map(({ group, parentLabelId }) => {
            const separatedGroups = separateGroup(group);

            if (separatedGroups.length > level) {
                return separatedGroups.slice(0, level).join(GROUP_SEPARATOR);
            }

            if (separatedGroups.length === level || isString(parentLabelId)) {
                return group;
            }

            return undefined;
        })
        .filter(isString);

    // All groups of the level
    const uniqueDescendantGroups = uniq([...descendantGroups]);

    return uniqueDescendantGroups.map((uniqueGroupName: string) => {
        const relation = getGroupRelation(labels, uniqueGroupName, parentId);
        const children = getChildItemsOfGroup(uniqueGroupName, labels, level, opened, parentId, relation);

        return {
            id: uniqueGroupName,
            name: getLowestLevelGroupName(uniqueGroupName),
            type: LabelItemType.GROUP,
            parentLabelId: parentId,
            open: true,
            relation,
            parentName: parentGroup,
            children,
            inEditMode: false,
            state: LabelItemEditionState.IDLE,
        } as LabelTreeItem;
    });
};

const getChildItemsOfGroup = (
    groupName: string,
    labels: ReadonlyArray<Label>,
    level: number,
    opened: string[] | 'all',
    parentLabelId: string | null,
    relation: LabelsRelationType
) => {
    const currentGroupLabels = getLabelsByGroup(labels, groupName, parentLabelId);
    const unusedLabels = labels.filter((label) => !currentGroupLabels.includes(label));
    const currentGroupLabelsHierarchical: LabelTreeItem[] = getGroupChildrenLabels(
        currentGroupLabels,
        unusedLabels,
        opened,
        level,
        relation
    );

    const groupChildrenGroupsNames = getUniqueChildGroupsNames(labels, groupName, parentLabelId);
    const currentGroupGroupsHierarchical: LabelTreeItem[] = getGroupChildrenGroups(
        groupChildrenGroupsNames,
        labels,
        opened,
        parentLabelId,
        { name: groupName, relation },
        level + 1
    );

    return [...currentGroupLabelsHierarchical, ...currentGroupGroupsHierarchical];
};
