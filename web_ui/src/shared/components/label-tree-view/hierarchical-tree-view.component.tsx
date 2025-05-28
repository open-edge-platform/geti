// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isEmpty } from 'lodash-es';

import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { HierarchicalLabelTreeViewProps, LabelTreeItem } from '../../../core/labels/label-tree-view.interface';
import { LabelTreeViewItem, LabelTreeViewItemProps } from './label-tree-view-item/label-tree-view-item.component';

import classes from './hierarchical-tree-view.module.scss';

export const HierarchicalTreeView = ({
    labels,
    isEditable,
    actions,
    projectLabels,
    level = 0,
    options,
    domains,
    treeValidationErrors,
    setValidationError,
}: HierarchicalLabelTreeViewProps): JSX.Element => {
    const { FEATURE_FLAG_LABELS_REORDERING } = useFeatureFlags();
    const reversedLabelList = FEATURE_FLAG_LABELS_REORDERING ? labels : [...labels].reverse();

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
                    actions,
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
                            actions={actions}
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
