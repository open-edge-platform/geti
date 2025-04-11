// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../../../../../../test-utils/required-providers-render';

import '@testing-library/jest-dom/extend-expect';

import { checkTooltip } from '../../../../../../../test-utils/utils';
import { StartOptimization } from './start-optimization.component';

const mockOptimizePOTModel = jest.fn();
jest.mock('../../../hooks/use-pot-model/use-pot-model.hook', () => ({
    usePOTModel: jest.fn(() => ({
        optimizePOTModel: mockOptimizePOTModel,
        isLoading: false,
    })),
}));

describe('StartOptimization', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    it('should render the button with correct label and call optimizePOTModel when button is clicked', () => {
        render(<StartOptimization isModelBeingOptimized={false} isDisabled={false} />);

        expect(screen.getByRole('button')).toHaveTextContent('Start optimization');

        fireEvent.click(screen.getByRole('button'));

        expect(mockOptimizePOTModel).toHaveBeenCalled();
    });

    it('should disable the button when isDisabled is true and show the tooltip with correct message when disabled', async () => {
        render(
            <StartOptimization
                isModelBeingOptimized={false}
                isDisabled={true}
                disabledTooltip='The button is disabled!'
            />
        );

        expect(screen.getByRole('button')).toBeDisabled();

        await checkTooltip(screen.getByRole('button', { name: 'Start optimization' }), /The button is disabled!/i);
    });
});
