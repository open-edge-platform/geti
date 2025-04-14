// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { checkSpectrumButtonTooltip } from '../../../test-utils/utils';
import { TooltipWithDisableButton } from './tooltip-with-disable-button';

describe('TooltipWithDisableButton', () => {
    it('should show the active tooltip if the child element is not disabled', () => {
        render(
            <TooltipWithDisableButton activeTooltip={'active tooltip'}>
                <button>Click me!</button>
            </TooltipWithDisableButton>
        );

        checkSpectrumButtonTooltip(screen.getByText(/Click me!/), 'active tooltip');
    });

    it('should show the disabled tooltip if the child element is disabled', () => {
        render(
            <TooltipWithDisableButton activeTooltip={'active tooltip'} disabledTooltip={'disabled tooltip'}>
                <button disabled>Click me!</button>
            </TooltipWithDisableButton>
        );

        checkSpectrumButtonTooltip(screen.getByText(/Click me!/), 'disabled tooltip');
    });
});
