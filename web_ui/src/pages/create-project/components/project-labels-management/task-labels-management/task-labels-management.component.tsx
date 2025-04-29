// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { Flex } from '@adobe/react-spectrum';

import {
    LabelItemEditionState,
    LabelItemType,
    LabelTreeItem,
    LabelTreeLabelProps,
    SetValidationProps,
    ValidationErrorType,
} from '../../../../../core/labels/label-tree-view.interface';
import { LabelsRelationType } from '../../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { TaskMetadata } from '../../../../../core/projects/task.interface';
import {
    getLabelsWithAddedChild,
    getLabelWithoutDeleted,
    getNextColor,
    getTreeWithUpdatedItem,
} from '../../../../../shared/components/label-tree-view/utils';
import { isYupValidationError } from '../../../../user-management/profile-page/utils';
import { validateLabelsSchema } from '../../../utils';
import { getHEXFormat } from '../../distinct-colors';
import { LABEL_TREE_TYPE } from '../label-tree-type.enum';
import { LabelTreeGroup } from './new-label-tree-item/label-tree-group.component';
import { LabelTreeLabel } from './new-label-tree-item/label-tree-label.component';
import { TaskLabelsCreationTree } from './task-labels-creation-tree/task-labels-creation-tree.component';

interface LabelsManagementProps {
    setLabels: (labels: LabelTreeItem[]) => void;
    setValidationError: (options: SetValidationProps) => void;
    type: LABEL_TREE_TYPE;
    taskMetadata: TaskMetadata;
    next: (() => void) | undefined;
    projectLabels: LabelTreeItem[];
    domains: DOMAIN[];
}

export const TaskLabelsManagement = ({
    setValidationError,
    type,
    setLabels,
    next,
    taskMetadata,
    projectLabels,
    domains,
}: LabelsManagementProps): JSX.Element => {
    const { labels, relation, domain } = taskMetadata;

    const singleLabel: LabelTreeLabelProps | undefined =
        type === LABEL_TREE_TYPE.SINGLE && labels.length === 1 ? (labels[0] as LabelTreeLabelProps) : undefined;
    const defaultName = singleLabel ? singleLabel.name : '';
    const defaultHotkey = singleLabel?.hotkey;
    const defaultColor = singleLabel ? getHEXFormat(singleLabel.color) : getNextColor(projectLabels);

    const setDialogValidationError = (message?: string) => {
        setValidationError({ type: ValidationErrorType.TREE, validationError: message });
    };

    const addChild = (parentId: string, groupName: string, childType: LabelItemType) => {
        setLabels(getLabelsWithAddedChild(labels, labels, parentId, groupName, childType));
    };

    const addLabel = (label: LabelTreeItem, shouldGoNext = false) => {
        const newLabel = { ...label, state: LabelItemEditionState.NEW };
        const newLabels: LabelTreeItem[] = type === LABEL_TREE_TYPE.SINGLE ? [newLabel] : [...labels, newLabel];

        setLabels(newLabels);

        if (type === LABEL_TREE_TYPE.SINGLE) {
            shouldGoNext && next && next();
        }
    };

    const saveHandler = (editedLabel?: LabelTreeItem, oldId?: string) => {
        const updated = getTreeWithUpdatedItem(labels, oldId, editedLabel, true);

        setLabels(updated);
    };

    const deleteItem = (deletedItem: LabelTreeItem) => {
        const updated = getLabelWithoutDeleted(labels, deletedItem);

        setLabels(updated);
    };

    useEffect(() => {
        try {
            const validated = validateLabelsSchema(domain).validateSync({ labels }, { abortEarly: false });

            setLabels(validated.labels || []);
            setValidationError({ type: ValidationErrorType.TREE, validationError: undefined });
        } catch (error: unknown) {
            if (isYupValidationError(error)) {
                setValidationError({ type: ValidationErrorType.TREE, validationError: error.errors.join('\r\n') });
            }
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [labels]);

    return (
        <>
            {relation === LabelsRelationType.MIXED ? (
                <LabelTreeGroup labels={labels} save={addLabel} parentGroupName={null} parentLabelId={null} />
            ) : (
                <LabelTreeLabel
                    type={type}
                    addLabel={addLabel}
                    color={defaultColor}
                    name={defaultName}
                    hotkey={defaultHotkey}
                    withLabel
                    projectLabels={projectLabels}
                    key={relation}
                    setDialogValidationError={setDialogValidationError}
                    domains={domains}
                    shouldFocus
                    taskMetadata={taskMetadata}
                    parentGroupName={null}
                />
            )}

            {type === LABEL_TREE_TYPE.SINGLE ? (
                <></>
            ) : (
                <Flex
                    id={'label-tree-view-container'}
                    direction={'column'}
                    maxHeight={'100%'}
                    height={'size-4600'}
                    minHeight={0}
                    UNSAFE_style={{
                        backgroundColor: 'var(--spectrum-global-color-gray-50)',
                        padding: 'var(--spectrum-global-dimension-size-300)',
                        overflow: 'auto',
                    }}
                >
                    <TaskLabelsCreationTree
                        isHierarchicalMode={relation === LabelsRelationType.MIXED}
                        labelsTree={labels}
                        addChild={addChild}
                        projectLabels={projectLabels}
                        domains={domains}
                        deleteItem={deleteItem}
                        save={saveHandler}
                        setValidationError={setValidationError}
                    />
                </Flex>
            )}
        </>
    );
};
