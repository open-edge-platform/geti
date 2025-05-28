// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useEffect, useMemo, useRef, useState } from 'react';

import { Flex } from '@geti/ui';

import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { getFullGroupName } from '../../../../core/labels/annotator-utils/group-utils';
import {
    LabelItemEditionState,
    LabelItemType,
    LabelTreeGroupProps,
    LabelTreeItem,
    LabelTreeLabelProps,
    TreeItemActions,
} from '../../../../core/labels/label-tree-view.interface';
import { filterGroups, filterLabels, getFlattenedItems } from '../../../../core/labels/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { isAnomalyDomain } from '../../../../core/projects/domains';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { LabelTreeViewGroup } from './label-tree-view-group.component';
import { Actions, LabelTreeViewItemMenu } from './label-tree-view-item-menu/label-tree-view-item-menu.component';
import { LabelTreeViewLabel } from './label-tree-view-label.component';
import { getItemId, isNew, isNewState, setRemovedStateToChildren } from './utils';

import classes from './label-tree-view-item.module.scss';

const attrs = {
    itemLink: {
        UNSAFE_className: `spectrum-TreeView-itemLink ${classes.viewCursor} ${classes.background}`,
    },
};

export interface LabelTreeViewItemProps {
    item: LabelTreeItem;
    children?: ReactNode;
    actions: TreeItemActions;
    projectLabels: LabelTreeItem[];
    isCreationInNewProject?: boolean;
    domains: DOMAIN[];
    isEditable: boolean;
    isMixedRelation: boolean;
    validationErrors: Record<string, string>;
    setValidationError: (id: string, validationErrors: Record<string, string>) => void;
}

export const LabelTreeViewItem = ({
    item,
    children,
    actions: { addChild, deleteItem, reorder, save },
    projectLabels,
    isCreationInNewProject = false,
    domains,
    isEditable,
    isMixedRelation,
    validationErrors,
    setValidationError,
}: LabelTreeViewItemProps): JSX.Element => {
    const { FEATURE_FLAG_LABELS_REORDERING } = useFeatureFlags();

    const [isOpen, setIsOpen] = useState<boolean>(item.open);
    const [inEditMode, setInEditMode] = useState<boolean>(item.inEditMode);

    const savedItem = useRef<LabelTreeItem>({ ...item });

    const isTaskChainProject = domains.length > 1;
    const isAnomalyProject = !isTaskChainProject && isAnomalyDomain(domains[0]);

    useEffect(() => {
        // If the node is closed and user want to add child item is opened
        // this is needed to show proper icon
        item.open !== isOpen && setIsOpen(item.open);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [item.open]);

    const flatProjectItems = useMemo(() => {
        return getFlattenedItems(projectLabels);
    }, [projectLabels]);

    const flatProjectLabels = useMemo(() => {
        return filterLabels(flatProjectItems);
    }, [flatProjectItems]);

    const flatProjectGroups = useMemo(() => {
        return filterGroups(flatProjectItems);
    }, [flatProjectItems]);

    const markAsRemoved = (deletedLabel: LabelTreeItem) => {
        save(
            {
                ...deletedLabel,
                state: deletedLabel.type === LabelItemType.LABEL ? LabelItemEditionState.REMOVED : deletedLabel.state,
                children: setRemovedStateToChildren(deletedLabel),
            },
            deletedLabel.id
        );
    };

    const deleteLabelHandler = () => {
        const isRemovable = isCreationInNewProject || isNewState(item.state);

        if (isRemovable) {
            deleteItem(item);
        } else {
            markAsRemoved(item);
        }
    };

    const addChildHandler = () => {
        if (item.type === LabelItemType.LABEL) {
            addChild(item.id, item.group, LabelItemType.GROUP);
        } else {
            addChild(item.parentLabelId, getFullGroupName(item.parentName, item.name), LabelItemType.LABEL);
        }
    };

    const onOpenClickHandler = () => {
        setIsOpen(!isOpen);
        save({ ...item, open: !isOpen }, item.id);
    };

    const finishEdition = () => {
        setInEditMode(false);
    };

    const saveHandler = (newItem: LabelTreeItem) => {
        save(newItem, item.id);
        finishEdition();
    };

    const reorderUpHandler = () => {
        reorder(item, 'up');
    };
    const reorderDownHandler = () => {
        reorder(item, 'down');
    };

    const isFlatStructure = !isMixedRelation;

    const isEditionModeOn = inEditMode || isEditable;
    const canEditItem = isCreationInNewProject || !(item.type === LabelItemType.GROUP && !isNew(item));

    const canReorderUp =
        FEATURE_FLAG_LABELS_REORDERING &&
        (item.type === LabelItemType.LABEL ? flatProjectLabels[0] : flatProjectGroups[0]).id !== item.id;

    const canReorderDown =
        FEATURE_FLAG_LABELS_REORDERING &&
        (item.type === LabelItemType.LABEL
            ? flatProjectLabels[flatProjectLabels.length - 1]
            : flatProjectGroups[flatProjectGroups.length - 1]
        ).id !== item.id;

    const canAddGroup =
        !isAnomalyProject &&
        !isFlatStructure &&
        domains.includes(DOMAIN.CLASSIFICATION) &&
        item.type === LabelItemType.LABEL;

    const canAddLabel = !isAnomalyProject && item.type === LabelItemType.GROUP;

    return (
        <li
            className={`spectrum-TreeView-item ${isOpen ? 'is-open' : classes.isClosed} ${classes.lightMode}`}
            id={getItemId(item)}
            aria-label={`label item ${item.name}`}
        >
            <div
                style={{ paddingBottom: '1px' }}
                aria-label={item.type === LabelItemType.GROUP ? `${item.name} group` : `${item.name} label`}
            >
                <Flex
                    UNSAFE_className={`${attrs.itemLink.UNSAFE_className} ${classes.treeViewItemLi}`}
                    data-testid={`item-link-${item.id}`}
                    alignItems={'center'}
                >
                    {item.type === LabelItemType.LABEL ? (
                        <LabelTreeViewLabel
                            item={item}
                            savedItem={savedItem.current as LabelTreeLabelProps}
                            save={saveHandler}
                            flatListProjectItems={flatProjectLabels}
                            newTree={isCreationInNewProject}
                            inEditionMode={isEditionModeOn && canEditItem}
                            isOpen={isOpen}
                            onOpenClickHandler={onOpenClickHandler}
                            domains={domains}
                            setValidationError={setValidationError}
                            validationErrors={validationErrors}
                        />
                    ) : (
                        <LabelTreeViewGroup
                            item={item}
                            savedItem={savedItem.current as LabelTreeGroupProps}
                            save={saveHandler}
                            flatListProjectItems={flatProjectGroups}
                            newTree={isCreationInNewProject}
                            inEditionMode={isEditionModeOn && canEditItem}
                            isOpen={isOpen}
                            onOpenClickHandler={onOpenClickHandler}
                            setValidationError={setValidationError}
                            validationErrors={validationErrors}
                        />
                    )}

                    <LabelTreeViewItemMenu
                        itemId={`${idMatchingFormat(item.name)}-${
                            item.type === LabelItemType.LABEL ? 'label' : 'group'
                        }`}
                        isAvailable={isEditable}
                        actions={{
                            [Actions.REORDER_UP]: {
                                isEnabled: canReorderUp,
                                onAction: reorderUpHandler,
                            },
                            [Actions.REORDER_DOWN]: {
                                isEnabled: canReorderDown,
                                onAction: reorderDownHandler,
                            },
                            [Actions.ADD_LABEL]: {
                                isEnabled: canAddLabel,
                                onAction: addChildHandler,
                            },
                            [Actions.ADD_GROUP]: {
                                isEnabled: canAddGroup,
                                onAction: addChildHandler,
                            },
                            [Actions.DELETE]: {
                                isEnabled: !isAnomalyProject,
                                onAction: deleteLabelHandler,
                            },
                        }}
                    />
                </Flex>
            </div>
            {item.children.length > 0 && children ? <>{children}</> : <></>}
        </li>
    );
};
