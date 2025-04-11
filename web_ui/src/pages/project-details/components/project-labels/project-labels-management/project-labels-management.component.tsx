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

import { Flex, View } from '@adobe/react-spectrum';

import {
    LabelItemEditionState,
    LabelItemType,
    LabelTreeItem,
    LabelTreeLabelProps,
    Readonly,
    SetValidationProps,
    ValidationErrorType,
} from '../../../../../core/labels/label-tree-view.interface';
import { LabelsRelationType } from '../../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { isAnomalyDomain } from '../../../../../core/projects/domains';
import { LabelTreeView } from '../../../../../shared/components/label-tree-view/label-tree-view.component';
import {
    getLabelsWithAddedChild,
    getLabelWithoutDeleted,
    getTreeWithUpdatedItem,
} from '../../../../../shared/components/label-tree-view/utils';
import { LABEL_TREE_TYPE } from '../../../../create-project/components/project-labels-management/label-tree-type.enum';
import { LabelTreeGroup } from '../../../../create-project/components/project-labels-management/task-labels-management/new-label-tree-item/label-tree-group.component';
import { LabelTreeLabel } from '../../../../create-project/components/project-labels-management/task-labels-management/new-label-tree-item/label-tree-label.component';

interface ProjectLabelsManagementProps {
    isInEdition: boolean;
    setIsDirty: (isDirty: boolean) => void;
    labelsTree: LabelTreeItem[];
    setLabelsTree: (labels: LabelTreeItem[]) => void;
    relation: LabelsRelationType;
    isTaskChainProject: boolean;
    domains: DOMAIN[];
    newItemNotAllowed?: boolean;
    id?: string;
    setLabelsValidity: (isValid: boolean) => void;
    parentLabel?: LabelTreeLabelProps;
}

export const ProjectLabelsManagement = ({
    isInEdition,
    setIsDirty,
    labelsTree,
    setLabelsTree,
    relation,
    isTaskChainProject,
    domains,
    newItemNotAllowed = false,
    id = '',
    setLabelsValidity,
    parentLabel,
}: ProjectLabelsManagementProps): JSX.Element => {
    const isAnomalyProject = !isTaskChainProject && isAnomalyDomain(domains[0]);

    const saveHandler = (editedLabel?: LabelTreeItem, oldId?: string) => {
        const updated = getTreeWithUpdatedItem(labelsTree, oldId, editedLabel);
        setTaskLabelsHandler(updated);
    };

    const addItemHandler = (item?: LabelTreeItem) => {
        item && setTaskLabelsHandler([...labelsTree, { ...item, state: LabelItemEditionState.NEW }]);
    };

    const addChild = (parentId: string, groupName: string, type: LabelItemType) => {
        setTaskLabelsHandler(getLabelsWithAddedChild(labelsTree, labelsTree, parentId, groupName, type));
    };

    const deleteItem = (deletedItem: LabelTreeItem) => {
        const updated = getLabelWithoutDeleted(labelsTree, deletedItem);

        setTaskLabelsHandler(updated);
    };

    const setTaskLabelsHandler = (updatedLabels: LabelTreeItem[]): void => {
        setLabelsTree(updatedLabels);
        setIsDirty(true);
    };

    const setValidationError = (options: SetValidationProps) => {
        if (options.type === ValidationErrorType.LABELS) {
            setLabelsValidity(!options.validationError);
        }
    };

    const isHierarchicalMode = relation === LabelsRelationType.MIXED;

    const shouldShowNewItem = !isAnomalyProject && isInEdition && !newItemNotAllowed;

    const shouldShowAddLabel = !isHierarchicalMode && shouldShowNewItem;
    const shouldShowAddGroup = isHierarchicalMode && shouldShowNewItem;

    // should focus label input only for non-classification project
    const shouldFocus = !domains.includes(DOMAIN.CLASSIFICATION);

    return (
        <>
            <View>
                {shouldShowAddGroup && (
                    <LabelTreeGroup
                        labels={labelsTree}
                        save={addItemHandler}
                        parentGroupName={parentLabel?.group ?? null}
                        parentLabelId={parentLabel?.id ?? null}
                    />
                )}
                {shouldShowAddLabel && (
                    // it does not appear in task chain projects
                    <LabelTreeLabel
                        type={LABEL_TREE_TYPE.FLAT}
                        addLabel={addItemHandler}
                        taskMetadata={{
                            labels: labelsTree,
                            relation,
                            domain: domains[0],
                        }}
                        name={''}
                        projectLabels={labelsTree}
                        key={relation}
                        domains={domains}
                        shouldFocus={shouldFocus}
                        parentGroupName={parentLabel?.group ?? null}
                    />
                )}
            </View>
            <Flex
                id={`labels-management-${id}-id`}
                width='100%'
                height='100%'
                direction='column'
                UNSAFE_style={{ overflow: 'auto scroll' }}
            >
                <LabelTreeView
                    labelsTree={labelsTree}
                    save={saveHandler}
                    deleteItem={deleteItem}
                    isInEditMode={isInEdition}
                    isHierarchicalMode={isHierarchicalMode}
                    addChild={addChild}
                    domains={domains}
                    setValidationError={setValidationError}
                    type={Readonly.NO}
                />
            </Flex>
        </>
    );
};
