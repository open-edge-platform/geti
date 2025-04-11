// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { EditableTreeViewProps, Readonly } from '../../../../../../core/labels/label-tree-view.interface';
import { LabelTreeView } from '../../../../../../shared/components/label-tree-view/label-tree-view.component';

type TaskLabelsCreationTreeProps = Omit<EditableTreeViewProps, 'type' | 'isInEditMode' | 'options'>;

export const TaskLabelsCreationTree = ({
    labelsTree,
    deleteItem,
    addChild,
    save,
    domains,
    isHierarchicalMode,
    projectLabels,
    setValidationError,
}: TaskLabelsCreationTreeProps): JSX.Element => {
    return (
        <LabelTreeView
            labelsTree={labelsTree}
            projectLabels={projectLabels}
            type={Readonly.NO}
            isHierarchicalMode={isHierarchicalMode}
            addChild={addChild}
            deleteItem={deleteItem}
            domains={domains}
            isInEditMode={true}
            options={{ newTree: true }}
            save={save}
            setValidationError={setValidationError}
        />
    );
};
