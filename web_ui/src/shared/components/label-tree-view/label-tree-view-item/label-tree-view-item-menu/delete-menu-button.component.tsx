// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Tooltip, TooltipTrigger } from '@geti/ui';

import { Delete } from '../../../../../assets/icons';
import { QuietActionButton } from '../../../quiet-button/quiet-action-button.component';
import { MenuButtonProps } from './menu-button.interface';

export const DeleteMenuButton = ({ action, id }: MenuButtonProps): JSX.Element => {
    return (
        <TooltipTrigger placement={'bottom'}>
            <QuietActionButton
                key={'delete-button'}
                onPress={action}
                id={`${id}-delete-label-button`}
                data-testid={`${id}-delete-label-button`}
            >
                <Delete aria-label={'delete'} width={'16px'} height={'16px'} />
            </QuietActionButton>
            <Tooltip>Remove</Tooltip>
        </TooltipTrigger>
    );
};
