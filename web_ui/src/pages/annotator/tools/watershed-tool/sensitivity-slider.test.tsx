// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import '@wessberg/pointer-events';

import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { checkTooltip } from '../../../../test-utils/utils';
import { SENSITIVITY_SLIDER_TOOLTIP } from '../utils';
import { SensitivitySlider } from './sensitivity-slider.component';

describe('SensitivitySlider', () => {
    afterAll(() => {
        jest.useRealTimers();
        jest.clearAllTimers();
    });

    beforeEach(() => jest.useFakeTimers());

    it('calls OnSelectSensitivity upon slide', () => {
        const mockOnSelectSensitivity = jest.fn();

        render(<SensitivitySlider max={3} value={1} onSelectSensitivity={mockOnSelectSensitivity} />);

        fireEvent.click(screen.getByRole('button', { name: 'Sensitivity button' }));

        const slider = screen.getByRole('slider');
        fireEvent.keyDown(slider, { key: 'Right' });

        expect(mockOnSelectSensitivity).toHaveBeenCalledWith(2);
    });

    it('calls OnSelectSensitivity with maxSensitivity', () => {
        const mockOnSelectSensitivity = jest.fn();
        const maxSensitivity = 3;

        render(
            <SensitivitySlider
                max={maxSensitivity}
                value={maxSensitivity + 10}
                onSelectSensitivity={mockOnSelectSensitivity}
            />
        );

        expect(mockOnSelectSensitivity).toHaveBeenCalledWith(maxSensitivity);
    });

    it('disabled with maxSensitivity equal to 1', async () => {
        const mockOnSelectSensitivity = jest.fn();

        render(<SensitivitySlider max={1} value={1} onSelectSensitivity={mockOnSelectSensitivity} />);

        const sensitivityButton = screen.getByTestId('sensitivity-button');

        const sliderWrapper = screen.getByTestId('slider-wrapper');

        await checkTooltip(
            sliderWrapper,
            `Image resolution is too low for a higher sensitivity. ${SENSITIVITY_SLIDER_TOOLTIP}`
        );

        expect(sensitivityButton).toBeDisabled();
    });

    it('should show tooltip when hovering sensitivity slider', async () => {
        render(<SensitivitySlider max={2} value={1} onSelectSensitivity={jest.fn()} />);

        await checkTooltip(screen.getByTestId('sensitivity-button'), SENSITIVITY_SLIDER_TOOLTIP);
    });
});
