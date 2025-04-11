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

import { fireEvent, render, screen } from '@testing-library/react';

import { MediaTextField } from './media-text-field.component';

jest.mock('lodash/debounce', () => (callback: (t: string) => void) => (value: string) => callback(value));

describe('MediaTextField', () => {
    const ariaLabel = 'input-text';

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('Render input text and uses textRegex for validation (invalid case)', () => {
        const emptyString = '';
        const invalidString = '----';
        const onSelectionChange = jest.fn();

        render(<MediaTextField ariaLabel={ariaLabel} onSelectionChange={onSelectionChange} />);

        const input = screen.getByLabelText(ariaLabel);

        fireEvent.input(input, { target: { value: invalidString } });

        expect(input.getAttribute('aria-invalid')).toBe('true');
        expect(onSelectionChange).toHaveBeenNthCalledWith(1, invalidString);

        fireEvent.input(input, { target: { value: emptyString } });

        expect(input.getAttribute('aria-invalid')).toBe('true');
        expect(onSelectionChange).toHaveBeenNthCalledWith(2, emptyString);
    });

    it('Render input text and uses textRegex for validation (valid case)', () => {
        const onSelectionChange = jest.fn();
        const testValue = 'test';

        render(<MediaTextField ariaLabel={ariaLabel} onSelectionChange={onSelectionChange} />);

        const input = screen.getByLabelText(ariaLabel);

        fireEvent.input(input, { target: { value: String(testValue) } });

        expect(input.getAttribute('aria-invalid')).toBe(null);
        expect(onSelectionChange).toHaveBeenNthCalledWith(1, testValue);
    });
});
