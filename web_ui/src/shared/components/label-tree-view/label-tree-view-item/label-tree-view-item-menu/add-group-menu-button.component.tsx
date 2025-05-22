// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, Tooltip, TooltipTrigger } from '@geti/ui';
import { AddGroup } from '@geti/ui/icons';

import { MenuButtonProps } from './menu-button.interface';

export const AddGroupMenuButton = ({ action, id }: MenuButtonProps): JSX.Element => {
    const elementId = `${id}-add-child-group-button`;

    return (
        <TooltipTrigger placement={'bottom'}>
            <ActionButton
                isQuiet
                key={elementId}
                onPress={action}
                id={elementId}
                data-testid={elementId}
                aria-label={'add child group button'}
            >
                <AddGroup aria-label={'add child'} width={'16px'} height={'16px'} />
            </ActionButton>
            <Tooltip>Add new group</Tooltip>
        </TooltipTrigger>
    );
};
