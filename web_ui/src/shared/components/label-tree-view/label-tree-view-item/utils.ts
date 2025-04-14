// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getLowestLevelGroupName } from '../../../../core/labels/annotator-utils/group-utils';
import { LabelItemEditionState, LabelItemType, LabelTreeItem } from '../../../../core/labels/label-tree-view.interface';
import { idMatchingFormat } from '../../../../test-utils/id-utils';

export const setRemovedStateToChildren = (currentItem: LabelTreeItem): LabelTreeItem[] => {
    return currentItem.children.map((child) => {
        return {
            ...child,
            state: child.type === LabelItemType.LABEL ? LabelItemEditionState.REMOVED : child.state,
            children: setRemovedStateToChildren(child),
        };
    });
};

export const DEFAULT_LABEL_INPUT_ERRORS = {
    name: '',
    hotkey: '',
};

export const DEFAULT_LABEL_INPUT_DIRTY = {
    name: false,
    hotkey: false,
};

enum Fields {
    NAME = 'name',
    HOTKEY = 'hotkey',
}

export type LabelFieldsErrors = {
    [key in Fields]: string;
};

export type LabelFieldsDirty = {
    [key in Fields]: boolean;
};

export const isNew = (item: LabelTreeItem): boolean => isNewState(item.state);
export const isNewState = (state: LabelItemEditionState): boolean => state.includes(LabelItemEditionState.NEW);

export const getItemId = (item: LabelTreeItem): string => {
    let id;

    const nameSuffix = `${idMatchingFormat(item.name)}-${item.type === LabelItemType.LABEL ? 'label' : 'group'}`;
    const suffix = nameSuffix;

    switch (item.type) {
        case LabelItemType.LABEL:
            id = `group-${getLowestLevelGroupName(item.group)}-${suffix}`;
            break;
        case LabelItemType.GROUP:
            id = `group-${nameSuffix}`;
            break;
    }

    return id;
};
