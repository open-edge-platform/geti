// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@geti/ui';

import { ICONS_SIZE_IN_REM, LABEL_ITEM_MENU_PLACEHOLDER_WIDTH } from '../../utils';
import { AddGroupMenuButton } from './add-group-menu-button.component';
import { AddLabelMenuButton } from './add-label-menu-button.component';
import { DeleteMenuButton } from './delete-menu-button.component';
import { ReorderMenuButton } from './reorder-menu-button.component';

export enum Actions {
    REORDER_UP,
    REORDER_DOWN,
    ADD_LABEL,
    ADD_GROUP,
    DELETE,
}

type ReorderActionType = Record<
    Actions.REORDER_UP | Actions.REORDER_DOWN,
    { isEnabled: boolean; isVisible: boolean; onAction: () => void }
>;

type ActionType = Record<
    Exclude<Actions, Actions.REORDER_DOWN & Actions.REORDER_UP>,
    { isVisible: boolean; onAction: () => void }
>;

interface LabelTreeViewItemMenuProps {
    isAvailable: boolean;

    actions: ReorderActionType & ActionType;
    itemId: string;
}

export const LabelTreeViewItemMenu = ({ isAvailable, actions, itemId }: LabelTreeViewItemMenuProps): JSX.Element => {
    return (
        <Flex
            minWidth={`${LABEL_ITEM_MENU_PLACEHOLDER_WIDTH}rem`}
            justifyContent={'end'}
            data-testid={`tree-item-menu-${itemId}`}
            minHeight={`${ICONS_SIZE_IN_REM}rem`}
            isHidden={!isAvailable}
        >
            <>
                {actions[Actions.REORDER_UP].isVisible && (
                    <ReorderMenuButton
                        action={actions[Actions.REORDER_UP].onAction}
                        id={itemId}
                        type={'up'}
                        isEnabled={actions[Actions.REORDER_UP].isEnabled}
                    />
                )}
                {actions[Actions.REORDER_DOWN].isVisible && (
                    <ReorderMenuButton
                        action={actions[Actions.REORDER_DOWN].onAction}
                        id={itemId}
                        type={'down'}
                        isEnabled={actions[Actions.REORDER_DOWN].isEnabled}
                    />
                )}
                {actions[Actions.ADD_LABEL].isVisible && (
                    <AddLabelMenuButton action={actions[Actions.ADD_LABEL].onAction} id={itemId} />
                )}
                {actions[Actions.ADD_GROUP].isVisible && (
                    <AddGroupMenuButton action={actions[Actions.ADD_GROUP].onAction} id={itemId} />
                )}
                {actions[Actions.DELETE].isVisible && (
                    <DeleteMenuButton action={actions[Actions.DELETE].onAction} id={itemId} />
                )}
            </>
        </Flex>
    );
};
