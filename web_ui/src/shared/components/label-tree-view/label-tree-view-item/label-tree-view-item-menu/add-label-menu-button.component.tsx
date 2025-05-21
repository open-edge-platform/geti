// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, Tooltip, TooltipTrigger } from '@geti/ui';
import { Add } from '@geti/ui/icons';

import { MenuButtonProps } from './menu-button.interface';

export const AddLabelMenuButton = ({ action, id }: MenuButtonProps): JSX.Element => {
    return (
        <TooltipTrigger placement={'bottom'}>
            <ActionButton
                isQuiet
                key={'add-child-label-button'}
                onPress={action}
                id={`${id}-add-child-label-button`}
                data-testid={`${id}-add-child-label-button`}
                aria-label={'add child label button'}
            >
                <Add aria-label={'add child'} width={'16px'} height={'16px'} />
            </ActionButton>
            <Tooltip>Add new label</Tooltip>
        </TooltipTrigger>
    );
};
