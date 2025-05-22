// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton } from '@geti/ui';
import { FitScreen } from '@geti/ui/icons';
import { useControls } from 'react-zoom-pan-pinch';

export const FitImageToScreenButton = (): JSX.Element => {
    const { resetTransform } = useControls();

    const handleFitImageToScreen = () => {
        resetTransform();
    };

    return (
        <ActionButton
            isQuiet
            key={'fit-image-to-screen-button'}
            id='fit-image-to-screen-button'
            aria-label='Fit image to screen'
            onPress={handleFitImageToScreen}
        >
            <FitScreen />
        </ActionButton>
    );
};
