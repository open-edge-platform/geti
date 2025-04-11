// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Refresh } from '../../../../../assets/icons';
import { TooltipWithDisableButton } from '../../../custom-tooltip/tooltip-with-disable-button';
import { QuietActionButton } from '../../../quiet-button/quiet-action-button.component';

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
            <QuietActionButton id={id} data-testid={id} isDisabled={isDisabled} onPress={handleResetButton}>
                <Refresh
                    fill={
                        isDisabled ? 'var(--spectrum-global-color-gray-500)' : 'var(--spectrum-global-color-gray-800)'
                    }
                    aria-label={'reset-icon'}
                    className={classes.resetIcon}
                />
            </QuietActionButton>
        </TooltipWithDisableButton>
    );
};
