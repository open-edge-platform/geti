// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, Tooltip, TooltipTrigger } from '@geti/ui';
import { Refresh } from '@geti/ui/icons';

import classes from './refresh-button.module.scss';

interface RefreshButtonProps {
    id: string;
    tooltip: string;
    ariaLabel: string;
    isLoading: boolean;
    onPress: () => void;
    isDisabled?: boolean;
}

export const RefreshButton = ({
    id,
    tooltip,
    onPress,
    ariaLabel,
    isLoading,
    isDisabled = isLoading,
}: RefreshButtonProps): JSX.Element => {
    return (
        <TooltipTrigger placement={'bottom'}>
            <ActionButton
                isQuiet
                id={id}
                aria-label={ariaLabel}
                isDisabled={isLoading || isDisabled}
                UNSAFE_className={`${isLoading ? classes.rotate : ''}`}
                onPress={onPress}
            >
                <Refresh />
            </ActionButton>
            <Tooltip>{tooltip}</Tooltip>
        </TooltipTrigger>
    );
};
