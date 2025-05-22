// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton } from '@geti/ui';
import { Refresh } from '@geti/ui/icons';

import { TooltipWithDisableButton } from '../../../custom-tooltip/tooltip-with-disable-button';

import classes from './reset-button.module.scss';

interface ResetButtonProps {
    isDisabled: boolean;
    handleResetButton: () => void;
    id: string;
}

export const ResetButton = ({ isDisabled, handleResetButton, id }: ResetButtonProps): JSX.Element => {
    return (
        <TooltipWithDisableButton
            placement={'bottom'}
            activeTooltip={'Resetting to default value'}
            disabledTooltip={'Resetting to default value'}
        >
            <ActionButton isQuiet id={id} data-testid={id} isDisabled={isDisabled} onPress={handleResetButton}>
                <Refresh
                    fill={
                        isDisabled ? 'var(--spectrum-global-color-gray-500)' : 'var(--spectrum-global-color-gray-800)'
                    }
                    aria-label={'reset-icon'}
                    className={classes.resetIcon}
                />
            </ActionButton>
        </TooltipWithDisableButton>
    );
};
