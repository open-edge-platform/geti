// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
