// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

        await checkTooltip(screen.getByLabelText('disabled tooltip trigger'), /The button is disabled!/i);
    });
});
