// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, Tooltip, TooltipTrigger } from '@geti/ui';
import { Delete } from '@geti/ui/icons';

import { MenuButtonProps } from './menu-button.interface';

export const DeleteMenuButton = ({ action, id }: MenuButtonProps): JSX.Element => {
    return (
        <TooltipTrigger placement={'bottom'}>
            <ActionButton
                isQuiet
                key={'delete-button'}
                onPress={action}
                id={`${id}-delete-label-button`}
                data-testid={`${id}-delete-label-button`}
            >
                <Delete aria-label={'delete'} width={'16px'} height={'16px'} />
            </ActionButton>
            <Tooltip>Remove</Tooltip>
        </TooltipTrigger>
    );
};
