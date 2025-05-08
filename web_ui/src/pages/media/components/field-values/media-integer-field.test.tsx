// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { MediaIntegerField } from './media-integer-field.component';

jest.mock('lodash-es', () => ({
    ...jest.requireActual('lodash-es'),
    debounce: (callback: (t: string) => void) => (value: string) => callback(value),
}));

describe('MediaNumberField', () => {
    const ariaLabel = 'Media number field';
    const onSelectionChange = jest.fn();

    const getIncreaseButton = () => screen.getByRole('button', { name: 'Increase value' });

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('Number greater than max allowed integer is invalid', () => {
        render(
            <MediaIntegerField
                isDisabled={false}
                ariaLabel={ariaLabel}
                initialValue={Number.MAX_SAFE_INTEGER}
                onSelectionChange={onSelectionChange}
            />
        );

        fireEvent.click(getIncreaseButton());

        expect(onSelectionChange).not.toHaveBeenCalled();
        expect(screen.getByTestId('media-integer-error-id')).toBeInTheDocument();
    });

    it('Number less than max allowed integer is valid', () => {
        render(
            <MediaIntegerField
                isDisabled={false}
                ariaLabel={ariaLabel}
                initialValue={0}
                onSelectionChange={onSelectionChange}
            />
        );

        fireEvent.click(getIncreaseButton());

        expect(onSelectionChange).toHaveBeenNthCalledWith(1, 1);
        expect(screen.queryByTestId('media-integer-error-id')).not.toBeInTheDocument();
    });
});
