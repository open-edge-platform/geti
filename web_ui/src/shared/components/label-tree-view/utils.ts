// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isEqual } from 'lodash-es';
import { v4 as uuidv4 } from 'uuid';

import { getEditedMultiLabelGroupName, getFullGroupName } from '../../../core/labels/annotator-utils/group-utils';
import {
    LabelItemEditionState,
    LabelItemType,
    LabelTreeGroupProps,
    LabelTreeItem,
    LabelTreeLabelProps,
} from '../../../core/labels/label-tree-view.interface';
import { Group, Label, LABEL_BEHAVIOUR, LabelsRelationType } from '../../../core/labels/label.interface';
import { getFlattenedItems, getFlattenedLabels } from '../../../core/labels/utils';
import { DOMAIN } from '../../../core/projects/core.interface';
import { getAvailableColors } from '../../../pages/project-details/components/project-labels/project-labels-management/utils';
import { hasDifferentId, hasEqualId } from '../../utils';
import { isNewState } from './label-tree-view-item/utils';

export const ICONS_SIZE_IN_REM = 3.2;
const MAX_AMOUNT_OF_ICONS = 3;
export const LABEL_ITEM_MENU_PLACEHOLDER_WIDTH = MAX_AMOUNT_OF_ICONS * ICONS_SIZE_IN_REM;
export const getDefaultGroupName = (domain: DOMAIN, parentGroup?: string | null) =>
    getFullGroupName(parentGroup ?? null, `${domain} labels`);

const getNewItemId = () => uuidv4();

export const getEditedItemState = (
    isNew: boolean,
    wasChanged: boolean,
    state: LabelItemEditionState
): LabelItemEditionState => {
    if (isNew) {
        return LabelItemEditionState.NEW;
    } else if (wasChanged) {
        return LabelItemEditionState.CHANGED;
    } else if (state === LabelItemEditionState.CHANGED) {
        return LabelItemEditionState.IDLE;
    } else {
        return state;
    }
};

export const getGroupBasedOnRelationType = (
    relationType: LabelsRelationType,
    defaultGroupName: string,
    labelName: string
): string => {
    const isSingleSelection = relationType === LabelsRelationType.SINGLE_SELECTION;

    return isSingleSelection ? defaultGroupName : getFullGroupName(defaultGroupName, labelName);
};

const getDistinctiveData = (item: LabelTreeItem) => {
    let meaningfulData: Label | Group;

    if (item.type === LabelItemType.LABEL) {
        const { name, parentLabelId, id, hotkey, group, color, behaviour, isEmpty, isBackground } = item;

        meaningfulData = {
            name,
            hotkey,
            group,
            color,
            parentLabelId,
            id,
            behaviour,
            isEmpty,
            isBackground,
        };
    } else {
        const { name, parentLabelId, id, parentName } = item;

        meaningfulData = {
            name,
            parentLabelId,
            id,
            parentName,
        };
    }

    return meaningfulData;
};

export const checkIfItemWasChanged = (item: LabelTreeItem, savedItem?: LabelTreeItem): boolean => {
    return !!savedItem && !isEqual(getDistinctiveData(item), getDistinctiveData(savedItem));
};

export const getEditedItem = (editedItemValues: LabelTreeItem, savedItemValues: LabelTreeItem): LabelTreeItem => {
    const { name, children, id, state, relation } = editedItemValues;
    const isNew = isNewState(state);
    const wasChanged = checkIfItemWasChanged(editedItemValues, savedItemValues);

    return {
        ...editedItemValues,
        id,
        state: getEditedItemState(isNew, wasChanged, state),
        children: children.map((child) => {
            const editedItem = {
                ...child,
                relation,
                parent: name,
                parentLabelId: id,
            };
            if (child.type === LabelItemType.LABEL && editedItemValues.type === LabelItemType.GROUP) {
                const fullGroupName = getFullGroupName(editedItemValues.parentName, name);

                const groupName = getEditedMultiLabelGroupName(
                    { ...editedItem, group: fullGroupName } as LabelTreeLabelProps,
                    savedItemValues?.relation,
                    isNew
                );

                return { ...editedItem, group: groupName };
            } else {
                return editedItem;
            }
        }),
    };
};

export const DEFAULT_LABEL = (options: {
    name: string;
    color: string;
    groupName: string;
    relation: LabelsRelationType;
    parentLabelId: string | null;
    inEditMode?: boolean;
    state?: LabelItemEditionState;
    hotkey?: string;
}): LabelTreeLabelProps => {
    const { name, color, groupName, relation, parentLabelId, inEditMode = true, state, hotkey } = options;

    return {
        name,
        id: getNewItemId(),
        color: color ? `${color.toLowerCase()}ff` : '#ededed',
        group: groupName,
        parentLabelId,
        open: true,
        children: [],
        hotkey,
        state: state || LabelItemEditionState.IDLE,
        inEditMode: inEditMode === undefined ? true : inEditMode,
        behaviour: LABEL_BEHAVIOUR.LOCAL + LABEL_BEHAVIOUR.GLOBAL,
        type: LabelItemType.LABEL,
        relation,
        isEmpty: false,
        isBackground: false,
    };
};

const DEFAULT_GROUP = (options: {
    name: string;
    relation: LabelsRelationType;
    parentLabelId?: string | null;
    inEditMode?: boolean;
    parentName: string | null;
    state?: LabelItemEditionState;
}): LabelTreeGroupProps => {
    const { name, relation, parentLabelId = null, inEditMode = true, parentName, state } = options;
    return {
        name,
        id: getNewItemId(),
        parentLabelId,
        parentName,
        open: true,
        children: [],
        inEditMode,
        relation,
        type: LabelItemType.GROUP,
        state: state || LabelItemEditionState.NEW,
    };
};

export const getNextColor = (labels: LabelTreeItem[]): string => {
    const availableColors = getAvailableColors(getFlattenedLabels(labels));
    const index = Math.floor(Math.random() * availableColors.length);
    return availableColors[index];
};

const getEditedLabelValue = (
    label: LabelTreeLabelProps,
    newValues?: LabelTreeLabelProps,
    projectCreation = false
): LabelTreeLabelProps => {
    const labelWithEditedValues = { ...label, ...newValues };
    const isNew = isNewState(label.state) || projectCreation;

    return {
        ...labelWithEditedValues,
        group: getEditedMultiLabelGroupName(labelWithEditedValues, label.relation, isNew),
    };
};

export const getTreeWithUpdatedItem = (
    currentLabels: LabelTreeItem[],
    updatedItemId?: string,
    newValues?: LabelTreeItem,
    projectCreation?: boolean
): LabelTreeItem[] => {
    return currentLabels.map((item: LabelTreeItem) => {
        if (item.id === updatedItemId) {
            if (item.type === LabelItemType.LABEL) {
                return getEditedLabelValue(item, newValues as LabelTreeLabelProps, projectCreation);
            }
            return { ...item, ...newValues } as LabelTreeGroupProps;
        } else {
            const children = getTreeWithUpdatedItem(item.children, updatedItemId, newValues, projectCreation);

            return {
                ...item,
                children,
            };
        }
    });
};

const getBaseName = (type: LabelItemType): string => {
    return type === LabelItemType.LABEL ? 'Label' : 'Group';
};

const getNewItemName = (type: LabelItemType, flatProjectItems: LabelTreeItem[]): string => {
    const base = getBaseName(type);

    return getUniqueItemName(base, flatProjectItems);
};

const getNewChildItem = (
    type: LabelItemType,
    parent: LabelTreeItem,
    groupName: string,
    flatProjectItems: LabelTreeItem[],
    defaultName: boolean
): LabelTreeItem => {
    const name = getNewItemName(type, flatProjectItems);
    const childGroupName = getGroupBasedOnRelationType(parent.relation, groupName, name);

    switch (type) {
        case LabelItemType.LABEL:
            return DEFAULT_LABEL({
                name,
                color: getNextColor(flatProjectItems),
                groupName: childGroupName,
                relation: parent.relation,
                parentLabelId: parent.parentLabelId,
                inEditMode: true,
                state: defaultName ? LabelItemEditionState.NEW_DEFAULT : LabelItemEditionState.NEW,
            });
        case LabelItemType.GROUP:
            return DEFAULT_GROUP({
                name,
                relation: LabelsRelationType.SINGLE_SELECTION,
                parentLabelId: parent.id,
                parentName: groupName,
                state: LabelItemEditionState.NEW,
            });
    }
};

export const getNewGroup = (
    name: string,
    relation: LabelsRelationType,
    flatProjectItems: LabelTreeItem[],
    parentName: string | null,
    parentLabelId: string | null
): LabelTreeGroupProps => {
    const newGroup = DEFAULT_GROUP({
        name,
        relation,
        inEditMode: false,
        parentName,
        parentLabelId,
        state: LabelItemEditionState.NEW,
    });

    const childGroupName = getFullGroupName(parentName, name);
    const children = [getNewChildItem(LabelItemType.LABEL, newGroup, childGroupName, flatProjectItems, true)];

    return { ...newGroup, children };
};

export const getLabelsWithAddedChild = (
    labelTree: LabelTreeItem[],
    currentLabel: LabelTreeItem[],
    parentId: string,
    groupName: string,
    type: LabelItemType
): LabelTreeItem[] => {
    return currentLabel.map((item: LabelTreeItem) => {
        const parentName = 'parentName' in item ? item.parentName : null;
        if (
            type === LabelItemType.LABEL ? getFullGroupName(parentName, item.name) === groupName : item.id === parentId
        ) {
            return {
                ...item,
                open: true,
                children: [
                    ...item.children,
                    getNewChildItem(type, item, groupName, getFlattenedItems(labelTree), true),
                ],
            };
        } else
            return {
                ...item,
                children: getLabelsWithAddedChild(labelTree, item.children, parentId, groupName, type),
            };
    });
};

export const getLabelWithoutDeleted = (labelTree: LabelTreeItem[], deletedItem: LabelTreeItem): LabelTreeItem[] => {
    if (labelTree.some(hasEqualId(deletedItem.id))) {
        return labelTree.filter(hasDifferentId(deletedItem.id));
    } else {
        return labelTree.map((item) => ({
            ...item,
            children: getLabelWithoutDeleted(item.children, deletedItem),
        }));
    }
};

const getUniqueItemName = <T extends { name: string }>(prefix: string, items: T[] = []) => {
    const getName = (index: number) => {
        return index > 1 ? `${prefix} ${index}` : prefix;
    };

    for (let index = 1; index <= items.length; index++) {
        const nameDoesExist = items.find(({ name }) => name.toLowerCase() === getName(index).toLowerCase());

        if (!nameDoesExist) {
            return getName(index);
        }
    }

    return getName(items.length + 1);
};
