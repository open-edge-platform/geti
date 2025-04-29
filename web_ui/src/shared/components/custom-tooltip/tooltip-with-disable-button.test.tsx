// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { providersRender as render } from '../../../test-utils/required-providers-render';
import { checkTooltip } from '../../../test-utils/utils';
import { ActionButton } from '../button/button.component';
import { TooltipWithDisableButton } from './tooltip-with-disable-button';

describe('TooltipWithDisableButton', () => {
    it('should show the active tooltip if the child element is not disabled', async () => {
        const tooltip = 'active tooltip';
        render(
            <TooltipWithDisableButton activeTooltip={tooltip}>
                <ActionButton>Click me!</ActionButton>
            </TooltipWithDisableButton>
        );

        await checkTooltip(screen.getByText(/Click me!/), tooltip);
    });

    it('should show the disabled tooltip if the child element is disabled', async () => {
        const disabledTooltip = 'disabled tooltip';
        render(
            <TooltipWithDisableButton activeTooltip={'active tooltip'} disabledTooltip={disabledTooltip}>
                <ActionButton isDisabled>Click me!</ActionButton>
            </TooltipWithDisableButton>
        );

        await checkTooltip(screen.getByLabelText('disabled tooltip trigger'), disabledTooltip);
    });
});
