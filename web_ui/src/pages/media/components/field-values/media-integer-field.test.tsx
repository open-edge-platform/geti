// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { MediaIntegerField } from './media-integer-field.component';

jest.mock('lodash/debounce', () => (callback: (t: string) => void) => (value: string) => callback(value));

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
