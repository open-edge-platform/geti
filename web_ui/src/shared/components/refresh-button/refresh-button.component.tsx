// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { Refresh } from '../../../assets/icons';
import { QuietActionButton } from '../quiet-button/quiet-action-button.component';

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
            <QuietActionButton
                id={id}
                aria-label={ariaLabel}
                isDisabled={isLoading || isDisabled}
                UNSAFE_className={`${isLoading ? classes.rotate : ''}`}
                onPress={onPress}
            >
                <Refresh />
            </QuietActionButton>
            <Tooltip>{tooltip}</Tooltip>
        </TooltipTrigger>
    );
};
