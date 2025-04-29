// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
