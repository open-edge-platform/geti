// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
