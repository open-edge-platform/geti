// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useMemo } from 'react';

import { TooltipWithDisableButton } from '@shared/components/custom-tooltip/tooltip-with-disable-button';
import { NumberSliderWithLocalHandler } from '@shared/components/number-slider/number-slider-with-local-handler.component';

import { SENSITIVITY_SLIDER_TOOLTIP } from '../utils';
import { SENSITIVITY_SLIDER_CONFIG } from './utils';

interface SensitivitySliderProps {
    max: number;
    value: number;
    onSelectSensitivity: (value: number) => void;
}

export const SensitivitySlider = ({ max, value, onSelectSensitivity }: SensitivitySliderProps): JSX.Element => {
    const maxSensitivity = useMemo(() => Math.min(SENSITIVITY_SLIDER_CONFIG.max, max), [max]);
    const isSmallSensitivity = maxSensitivity === 1;

    useEffect(() => {
        if (value > maxSensitivity) {
            onSelectSensitivity(maxSensitivity);
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [value, maxSensitivity]);

    return (
        <TooltipWithDisableButton
            placement={'bottom'}
            activeTooltip={SENSITIVITY_SLIDER_TOOLTIP}
            disabledTooltip={`Image resolution is too low for a higher sensitivity.\n${SENSITIVITY_SLIDER_TOOLTIP}`}
        >
            <NumberSliderWithLocalHandler
                id='sensitivity'
                label={'Sensitivity'}
                ariaLabel='Sensitivity'
                value={value}
                isDisabled={isSmallSensitivity}
                max={maxSensitivity}
                onChange={onSelectSensitivity}
                min={SENSITIVITY_SLIDER_CONFIG.min}
                step={SENSITIVITY_SLIDER_CONFIG.step}
                displayText={(sensitivity) => sensitivity}
                changeAdHoc
            />
        </TooltipWithDisableButton>
    );
};
