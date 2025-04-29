// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@adobe/react-spectrum';

import { ICONS_SIZE_IN_REM, LABEL_ITEM_MENU_PLACEHOLDER_WIDTH } from '../../utils';
import { AddGroupMenuButton } from './add-group-menu-button.component';
import { AddLabelMenuButton } from './add-label-menu-button.component';
import { DeleteMenuButton } from './delete-menu-button.component';

export enum Actions {
    ADD_LABEL,
    ADD_GROUP,
    DELETE,
}

interface LabelTreeViewItemMenuProps {
    isAvailable: boolean;
    actions: Record<Actions, { isEnabled: boolean; onAction: () => void }>;
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
                {actions[Actions.ADD_LABEL].isEnabled && (
                    <AddLabelMenuButton action={actions[Actions.ADD_LABEL].onAction} id={itemId} />
                )}
                {actions[Actions.ADD_GROUP].isEnabled && (
                    <AddGroupMenuButton action={actions[Actions.ADD_GROUP].onAction} id={itemId} />
                )}
                {actions[Actions.DELETE].isEnabled && (
                    <DeleteMenuButton action={actions[Actions.DELETE].onAction} id={itemId} />
                )}
            </>
        </Flex>
    );
};
