// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
