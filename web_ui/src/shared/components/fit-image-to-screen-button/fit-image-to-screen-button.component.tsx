// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useControls } from 'react-zoom-pan-pinch';

import { FitScreen } from '../../../assets/icons';
import { QuietActionButton } from '../quiet-button/quiet-action-button.component';

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
