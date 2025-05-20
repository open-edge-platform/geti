// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Tooltip, TooltipTrigger } from '@geti/ui';

import { Add } from '../../../../../assets/icons';
import { QuietActionButton } from '../../../quiet-button/quiet-action-button.component';
import { MenuButtonProps } from './menu-button.interface';

export const AddLabelMenuButton = ({ action, id }: MenuButtonProps): JSX.Element => {
    return (
        <TooltipTrigger placement={'bottom'}>
            <QuietActionButton
                key={'add-child-label-button'}
                onPress={action}
                id={`${id}-add-child-label-button`}
                data-testid={`${id}-add-child-label-button`}
                aria-label={'add child label button'}
            >
                <Add aria-label={'add child'} width={'16px'} height={'16px'} />
            </QuietActionButton>
            <Tooltip>Add new label</Tooltip>
        </TooltipTrigger>
    );
};
