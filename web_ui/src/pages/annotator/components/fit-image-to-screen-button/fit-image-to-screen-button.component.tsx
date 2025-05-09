// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useControls } from 'react-zoom-pan-pinch';

import { FitScreen } from '../../../../assets/icons';
import { QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';

export const FitImageToScreenButton = (): JSX.Element => {
    const { resetTransform } = useControls();

    const handleFitImageToScreen = () => {
        resetTransform();
    };

    return (
        <QuietActionButton
            key={'fit-image-to-screen-button'}
            id='fit-image-to-screen-button'
            aria-label='Fit image to screen'
            onPress={handleFitImageToScreen}
        >
            <FitScreen />
        </QuietActionButton>
    );
};
