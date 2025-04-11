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

import { NumberSlider } from '../../../../shared/components/number-slider/number-slider.component';
import { brushSizeSliderConfig } from './utils';
import { useWatershedState } from './watershed-state-provider.component';

interface BrushSizeSliderProps {
    updateBrushSize: (value: number) => void;
}

export const BrushSizeSlider = ({ updateBrushSize }: BrushSizeSliderProps): JSX.Element => {
    const { brushSize, setBrushSize, setIsBrushSizePreviewVisible } = useWatershedState();

    const handleOnChange = (value: number): void => {
        setIsBrushSizePreviewVisible(true);
        setBrushSize(value);
    };

    const handleOnChangeEnd = (value: number): void => {
        setIsBrushSizePreviewVisible(false);
        updateBrushSize(value);
    };

    return (
        <NumberSlider
            id='brush-size'
            onChange={handleOnChange}
            onChangeEnd={handleOnChangeEnd}
            displayText={(value) => `${value}px`}
            label={'Brush size'}
            ariaLabel='Brush size'
            min={brushSizeSliderConfig.min}
            max={brushSizeSliderConfig.max}
            step={brushSizeSliderConfig.step}
            value={brushSize}
        />
    );
};
