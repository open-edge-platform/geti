// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
