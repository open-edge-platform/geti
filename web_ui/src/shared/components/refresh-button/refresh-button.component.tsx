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
