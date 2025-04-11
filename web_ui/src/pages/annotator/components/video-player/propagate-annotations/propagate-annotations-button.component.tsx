// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ActionButton } from '../../../../../shared/components/button/button.component';
import { TooltipWithDisableButton } from '../../../../../shared/components/custom-tooltip/tooltip-with-disable-button';
import { PropagateAnnotationsIcon } from './propagate-annotations-icon.component';

interface PropagateAnnotationsButtonProps {
    isDisabled: boolean;
    onPress?: () => void;
}

export const PropagateAnnotationsButton = ({ isDisabled, onPress }: PropagateAnnotationsButtonProps): JSX.Element => {
    return (
        <TooltipWithDisableButton
            placement={'top'}
            activeTooltip={'Propagate annotations from current frame to next frame'}
            disabledTooltip={'Propagate annotations from current frame to next frame'}
        >
            <ActionButton
                isQuiet
                isDisabled={isDisabled}
                onPress={onPress}
                id='video-player-propagate-annotations'
                aria-label='Propagate annotations from current frame to next frame'
            >
                <PropagateAnnotationsIcon />
            </ActionButton>
        </TooltipWithDisableButton>
    );
};
