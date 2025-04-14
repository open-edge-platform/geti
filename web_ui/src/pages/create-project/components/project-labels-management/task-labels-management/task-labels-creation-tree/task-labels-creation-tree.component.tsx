// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
