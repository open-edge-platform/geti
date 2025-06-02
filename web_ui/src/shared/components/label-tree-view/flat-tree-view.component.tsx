// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FlatLabelTreeViewProps, LabelItemType, LabelTreeItem } from '../../../core/labels/label-tree-view.interface';
import { LabelTreeViewItem } from './label-tree-view-item/label-tree-view-item.component';

export const FlatTreeView = ({
    treeItems,
    isEditable,
    actions,
    projectLabels,
    width,
    isCreationInNewProject = false,
    domains,
    treeValidationErrors,
    setValidationError,
}: FlatLabelTreeViewProps): JSX.Element => {
    const labels =
        treeItems.length > 0 ? (treeItems[0].type === LabelItemType.GROUP ? treeItems[0].children : treeItems) : [];

    return (
        <ul
            className={`spectrum-TreeView ${isEditable ? 'spectrum-TreeView--thumbnail' : ''}`}
            style={{ margin: 0, maxWidth: width || '100%' }}
        >
            {labels.map((label: LabelTreeItem) => {
                return (
                    <LabelTreeViewItem
                        key={label.id}
                        item={label}
                        siblings={labels}
                        actions={actions}
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
