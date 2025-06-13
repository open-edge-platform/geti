// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { isEmpty } from 'lodash-es';

import {
    CommonTreeViewProps,
    LabelsTreeViewProps,
    LabelTreeItem,
    Readonly,
    ValidationErrorType,
} from '../../../core/labels/label-tree-view.interface';
import { getFlattenedItems } from '../../../core/labels/utils';
import { getIds, hasEqualId } from '../../utils';
import { FlatTreeView } from './flat-tree-view.component';
import { HierarchicalTreeView } from './hierarchical-tree-view.component';

export const LabelTreeView = (props: LabelsTreeViewProps): JSX.Element => {
    const { type, labelsTree, actions, domains = [], projectLabels = labelsTree, options } = props;
    const isEditable = type === Readonly.NO ? props.isInEditMode : false;
    const setLabelsValidationError = type === Readonly.NO ? props.setValidationError : false;
    const [treeItemsValidationErrors, setTreeItemsValidationErrors] = useState<Record<string, Record<string, string>>>(
        {}
    );

    const setLabelValidationError = (id: string, validationErrors: Record<string, string>) => {
        let newValidationErrors: Record<string, Record<string, string>>;
        // We could pass "item" as an argument to this function instead of "id" but then all
        // interfaces and other utils would have to be updated. So we opted to make this check
        // localized.
        const labelItem = getFlattenedItems(projectLabels).find(hasEqualId(id));

        if (isEmpty(validationErrors)) {
            newValidationErrors = { ...treeItemsValidationErrors };

            delete newValidationErrors[id];

            // This means that the item is a GROUP item.
            // So we have to also delete all errors from its descendants
            if (!isEmpty(labelItem) && !isEmpty(labelItem.children)) {
                const allLabelDescendantIds = getIds(getFlattenedItems(labelItem?.children));

                allLabelDescendantIds.forEach((descendantId) => {
                    delete newValidationErrors[descendantId];
                });
            }
        } else {
            newValidationErrors = {
                ...treeItemsValidationErrors,
                [id]: validationErrors,
            };
        }

        setTreeItemsValidationErrors(newValidationErrors);
        setLabelsValidationError &&
            setLabelsValidationError({
                type: ValidationErrorType.LABELS,
                validationError: !isEmpty(newValidationErrors),
            });
    };

    const deleteItemHandler = (deletedItem: LabelTreeItem) => {
        // Clear validation errors from deleted item
        setLabelValidationError(deletedItem.id, {});
        actions.deleteItem(deletedItem);
    };

    const parameters: CommonTreeViewProps = {
        treeItems: labelsTree,
        isEditable,
        actions: {
            ...actions,
            deleteItem: deleteItemHandler,
        },
        projectLabels,
        domains,
        treeValidationErrors: treeItemsValidationErrors,
        setValidationError: setLabelValidationError,
    };

    return props.isHierarchicalMode ? (
        <HierarchicalTreeView options={options} {...parameters} />
    ) : (
        <FlatTreeView isCreationInNewProject={options?.newTree} {...parameters} />
    );
};
