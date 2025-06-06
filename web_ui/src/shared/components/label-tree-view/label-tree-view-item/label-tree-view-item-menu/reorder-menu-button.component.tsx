// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, Tooltip, TooltipTrigger } from '@geti/ui';
import { SortDown, SortUp } from '@geti/ui/icons';

import { MenuButtonProps } from './menu-button.interface';

interface ReorderMenuButtonProps extends MenuButtonProps {
    type: 'up' | 'down';
    isEnabled: boolean;
}

export const ReorderMenuButton = ({ action, id, type, isEnabled }: ReorderMenuButtonProps): JSX.Element => {
    const reorderButtonId = `reorder-${type}-label-button`;

    return (
        <TooltipTrigger placement={'bottom'}>
            <ActionButton
                isQuiet
                key={reorderButtonId}
                onPress={action}
                id={`${id}-${reorderButtonId}`}
                data-testid={`${id}-${reorderButtonId}`}
                aria-label={`reorder ${type} label button`}
                isDisabled={!isEnabled}
            >
                {type === 'up' ? (
                    <SortUp aria-label={'reorder up'} width={'16px'} height={'16px'} />
                ) : (
                    <SortDown aria-label={'reorder down'} width={'16px'} height={'16px'} />
                )}
            </ActionButton>
            <Tooltip>Reorder label {type}</Tooltip>
        </TooltipTrigger>
    );
};
