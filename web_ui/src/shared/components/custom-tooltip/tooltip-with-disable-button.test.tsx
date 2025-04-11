// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
