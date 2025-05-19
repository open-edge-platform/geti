// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Tooltip, TooltipTrigger } from '@geti/ui';

import { AddGroup } from '../../../../../assets/icons';
import { QuietActionButton } from '../../../quiet-button/quiet-action-button.component';
import { MenuButtonProps } from './menu-button.interface';

export const AddGroupMenuButton = ({ action, id }: MenuButtonProps): JSX.Element => {
    const elementId = `${id}-add-child-group-button`;

    return (
        <TooltipTrigger placement={'bottom'}>
            <QuietActionButton
                key={elementId}
                onPress={action}
                id={elementId}
                data-testid={elementId}
                aria-label={'add child group button'}
            >
                <AddGroup aria-label={'add child'} width={'16px'} height={'16px'} />
            </QuietActionButton>
            <Tooltip>Add new group</Tooltip>
        </TooltipTrigger>
    );
};
