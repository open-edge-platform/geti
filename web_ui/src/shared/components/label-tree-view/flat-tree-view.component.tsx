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

import { FlatLabelTreeViewProps, LabelItemType, LabelTreeItem } from '../../../core/labels/label-tree-view.interface';
import { LabelTreeViewItem } from './label-tree-view-item/label-tree-view-item.component';

export const FlatTreeView = ({
    labels,
    isEditable,
    save,
    addChild,
    deleteItem,
    projectLabels,
    width,
    isCreationInNewProject = false,
    domains,
    treeValidationErrors,
    setValidationError,
}: FlatLabelTreeViewProps): JSX.Element => {
    const onlyLabels = labels.length > 0 ? (labels[0].type === LabelItemType.GROUP ? labels[0].children : labels) : [];

    const reversedLabelList = [...onlyLabels].reverse();

    return (
        <ul
            className={`spectrum-TreeView ${isEditable ? 'spectrum-TreeView--thumbnail' : ''}`}
            style={{ margin: 0, maxWidth: width || '100%' }}
        >
            {reversedLabelList.map((label: LabelTreeItem) => {
                return (
                    <LabelTreeViewItem
                        key={label.id}
                        item={label}
                        save={save}
                        addChild={addChild}
                        deleteItem={deleteItem}
                        projectLabels={projectLabels}
                        isCreationInNewProject={isCreationInNewProject}
                        domains={domains}
                        isEditable={isEditable}
                        isMixedRelation={false}
                        validationErrors={treeValidationErrors[label.id]}
                        setValidationError={setValidationError}
                    />
                );
            })}
        </ul>
    );
};
