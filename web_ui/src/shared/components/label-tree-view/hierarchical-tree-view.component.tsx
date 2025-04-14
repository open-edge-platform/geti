// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isEmpty from 'lodash/isEmpty';

import { HierarchicalLabelTreeViewProps, LabelTreeItem } from '../../../core/labels/label-tree-view.interface';
import { LabelTreeViewItem, LabelTreeViewItemProps } from './label-tree-view-item/label-tree-view-item.component';

import classes from './hierarchical-tree-view.module.scss';

export const HierarchicalTreeView = ({
    labels,
    isEditable,
    save,
    addChild,
    deleteItem,
    projectLabels,
    level = 0,
    options,
    domains,
    treeValidationErrors,
    setValidationError,
}: HierarchicalLabelTreeViewProps): JSX.Element => {
    const reversedLabelList = [...labels].reverse();

    return (
        <ul
            className={`spectrum-TreeView ${isEditable ? 'spectrum-TreeView--thumbnail' : ''} ${classes.item}`}
            style={{
                maxWidth: options?.width || '100%',
                paddingLeft: level && 'var(--spectrum-global-dimension-size-500)',
            }}
        >
            {reversedLabelList.map((item: LabelTreeItem) => {
                const labelTreeViewItemProps: LabelTreeViewItemProps = {
                    save,
                    addChild,
                    deleteItem,
                    setValidationError,
                    item,
                    domains,
                    isEditable,
                    projectLabels,
                    isMixedRelation: true,
                    isCreationInNewProject: options?.newTree,
                    validationErrors: treeValidationErrors[item.id],
                };

                if (isEmpty(item.children)) {
                    return <LabelTreeViewItem key={item.id} {...labelTreeViewItemProps} />;
                }

                return (
                    <LabelTreeViewItem key={item.id} {...labelTreeViewItemProps}>
                        <HierarchicalTreeView
                            labels={item.children}
                            isEditable={isEditable}
                            options={options}
                            save={save}
                            addChild={addChild}
                            deleteItem={deleteItem}
                            projectLabels={projectLabels}
                            level={++level}
                            domains={domains}
                            treeValidationErrors={treeValidationErrors}
                            setValidationError={setValidationError}
                        />
                    </LabelTreeViewItem>
                );
            })}
        </ul>
    );
};
