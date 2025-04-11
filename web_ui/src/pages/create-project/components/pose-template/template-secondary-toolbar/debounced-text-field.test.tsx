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

import { fireEvent, render, screen } from '@testing-library/react';

import { DebouncedTextField } from './debounced-text-field.component';

describe('DebouncedTextField', () => {
    beforeAll(() => {
        jest.useFakeTimers();
    });

    afterAll(() => {
        jest.useRealTimers();
        jest.clearAllTimers();
    });

    it('calls onChange and onChangeEnd with debounced value', () => {
        const mockedOnChange = jest.fn();
        const mockedOnChangeEnd = jest.fn();
        const delay = 300;

        render(<DebouncedTextField onChange={mockedOnChange} onChangeEnd={mockedOnChangeEnd} delay={delay} />);

        fireEvent.change(screen.getByRole('textbox'), { target: { value: 'test' } });

        expect(mockedOnChange).toHaveBeenCalledWith('test');
        expect(mockedOnChangeEnd).not.toHaveBeenCalled();

        jest.advanceTimersByTime(delay);

        expect(mockedOnChangeEnd).toHaveBeenCalledWith('test');
    });
});
