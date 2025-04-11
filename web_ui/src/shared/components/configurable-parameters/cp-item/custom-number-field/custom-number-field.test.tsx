// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useState } from 'react';

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { CustomNumberField } from './custom-number-field.component';

describe('CustomNumberField', () => {
    it('Set value in range', async () => {
        render(
            <CustomNumberField
                defaultValue={0.01}
                value={0.001}
                onChange={jest.fn()}
                step={0.1}
                maxValue={1}
                minValue={0.0001}
                formatOptions={{}}
                aria-label='test'
            />
        );

        expect(screen.getByRole('textbox')).toHaveValue('0.001');
    });

    it('Set value higher than maximum', async () => {
        render(
            <CustomNumberField
                defaultValue={1}
                value={5}
                onChange={jest.fn()}
                step={0.1}
                maxValue={10}
                minValue={0}
                formatOptions={{}}
                aria-label='test'
                isValueChangedAdHoc
            />
        );

        const input = screen.getByRole('textbox');
        fireEvent.change(input, { target: { value: '50' } });

        await waitFor(() => {
            expect(input).toHaveValue('10');
        });

        const button = screen.getAllByRole('button')[0];
        fireEvent.click(button);

        expect(input).toHaveValue('10');
    });

    it('Set value lower than minimum', async () => {
        render(
            <CustomNumberField
                defaultValue={1}
                value={7}
                onChange={jest.fn()}
                step={0.1}
                maxValue={10}
                minValue={5}
                formatOptions={{}}
                aria-label='test'
                isValueChangedAdHoc
            />
        );

        const input = screen.getByRole('textbox');

        fireEvent.change(input, { target: { value: '0' } });
        await waitFor(() => {
            expect(input).toHaveValue('5');
        });
    });

    it('Set maximum value - up arrow should be disabled', async () => {
        render(
            <CustomNumberField
                defaultValue={1}
                value={10}
                onChange={jest.fn()}
                step={0.1}
                maxValue={10}
                minValue={0}
                formatOptions={{}}
                aria-label='test'
            />
        );

        const buttons = screen.getAllByRole('button');

        expect(buttons[0]).toBeDisabled();
        expect(buttons[1]).toBeEnabled();
    });

    it('Set minimum value - down arrow should be disabled', async () => {
        render(
            <CustomNumberField
                defaultValue={1}
                value={0}
                onChange={jest.fn()}
                step={0.1}
                maxValue={10}
                minValue={0}
                formatOptions={{}}
                aria-label='test'
            />
        );

        const buttons = screen.getAllByRole('button');
        const up = buttons[0];
        const down = buttons[1];
        expect(down).toBeDisabled();
        expect(up).toBeEnabled();
    });

    it('Set value 1.23K and click down and up arrow', async () => {
        let value = 1230;
        const onChangeMock = jest.fn((result) => {
            value = result;
        });

        render(
            <CustomNumberField
                defaultValue={1}
                value={value}
                onChange={onChangeMock}
                step={20}
                maxValue={2000}
                minValue={0}
                formatOptions={{ notation: 'compact', compactDisplay: 'short', minimumFractionDigits: 2 }}
                aria-label='test'
            />
        );

        const input = screen.getByRole('textbox');
        expect(input).toHaveValue('1.23K');
        const buttons = screen.getAllByRole('button');

        fireEvent.click(buttons[0]);
        expect(input).toHaveValue('1.25K');
        fireEvent.click(buttons[1]);
        expect(input).toHaveValue('1.23K');
    });

    it('Set value 1T and click down and up arrow', async () => {
        let value = 1000000000000;
        const onChangeMock = jest.fn((result) => {
            value = result;
        });

        render(
            <CustomNumberField
                defaultValue={1}
                value={value}
                onChange={onChangeMock}
                step={500000000000}
                maxValue={2000000000000}
                minValue={0}
                formatOptions={{ notation: 'compact', compactDisplay: 'short', minimumFractionDigits: 0 }}
                aria-label='test'
            />
        );

        const input = screen.getByRole('textbox');
        expect(input).toHaveValue('1T');
        const buttonUp = screen.getByRole('button', { name: 'Increase value' });
        const buttonDown = screen.getByRole('button', { name: 'Decrease value' });

        fireEvent.click(buttonUp);
        expect(input).toHaveValue('1.5T');
        fireEvent.click(buttonDown);
        expect(input).toHaveValue('1T');
    });

    it('Set value in range and check up and down arrow', async () => {
        let value = 23;
        const onChangeMock = jest.fn((result) => {
            value = result;
        });

        render(
            <CustomNumberField
                defaultValue={1}
                value={value}
                onChange={onChangeMock}
                step={1}
                maxValue={50}
                minValue={0}
                formatOptions={{ notation: 'compact', compactDisplay: 'short', minimumFractionDigits: 0 }}
                aria-label='test'
            />
        );

        const input = screen.getByRole('textbox');
        const buttonUp = screen.getByRole('button', { name: 'Increase value' });
        const buttonDown = screen.getByRole('button', { name: 'Decrease value' });

        fireEvent.click(buttonUp);
        expect(input).toHaveValue('24');
        fireEvent.click(buttonDown);
        expect(input).toHaveValue('23');
    });

    it('Type not proper value - abcd*( - nothing should appear', async () => {
        let value = 23;
        const onChangeMock = jest.fn((result) => {
            value = result;
        });

        render(
            <CustomNumberField
                defaultValue={1}
                value={value}
                onChange={onChangeMock}
                step={1}
                maxValue={2000}
                minValue={0}
                formatOptions={{ notation: 'compact', compactDisplay: 'short' }}
                aria-label='test'
                isValueChangedAdHoc
            />
        );

        const input = screen.getByRole('textbox');

        fireEvent.change(input, { target: { value: '' } });
        await waitFor(() => {
            expect(input).toHaveValue('');
        });
        fireEvent.change(input, { target: { value: 'abcd*(' } });

        await waitFor(() => {
            expect(input).toHaveValue('');
        });
    });

    it('Type not proper value - 23abcd*( - should stay 23', async () => {
        let value = 23;
        const onChangeMock = jest.fn((result) => {
            value = result;
        });

        render(
            <CustomNumberField
                defaultValue={1}
                value={value}
                onChange={onChangeMock}
                step={1}
                maxValue={2000}
                minValue={0}
                formatOptions={{ notation: 'compact', compactDisplay: 'short' }}
                aria-label='test'
                isValueChangedAdHoc
            />
        );

        const input = screen.getByRole('textbox');
        fireEvent.change(input, { target: { value: '23abcd*(' } });
        await waitFor(() => {
            expect(input).toHaveValue('23');
        });
    });

    it('Set 0.00000001 and check if it is properly displayed', async () => {
        let value = 0.0000001;
        const onChangeMock = jest.fn((result) => {
            value = result;
        });

        render(
            <CustomNumberField
                defaultValue={1}
                value={value}
                onChange={onChangeMock}
                step={0.001}
                maxValue={0.1}
                minValue={0.0000001}
                formatOptions={{ notation: 'compact', compactDisplay: 'short', maximumFractionDigits: 7 }}
                aria-label='test'
            />
        );

        const input = screen.getByRole('textbox');

        expect(input).toHaveValue('0.0000001');
    });

    it("Doesn't reset value when rerendering", async () => {
        const App = () => {
            const rerenderState = useState(0);

            return (
                <>
                    <CustomNumberField
                        defaultValue={1}
                        value={1230}
                        onChange={jest.fn()}
                        step={20}
                        maxValue={2000}
                        minValue={0}
                        formatOptions={{ notation: 'compact', compactDisplay: 'short', minimumFractionDigits: 2 }}
                        aria-label='test'
                    />
                    <button onClick={() => rerenderState[1]((x) => x + 1)}>Rerender</button>
                </>
            );
        };

        render(<App />);

        const input = screen.getByRole('textbox');
        expect(input).toHaveValue('1.23K');

        fireEvent.click(screen.getByRole('button', { name: 'Increase value' }));
        expect(input).toHaveValue('1.25K');

        fireEvent.click(screen.getByRole('button', { name: 'Rerender' }));
        expect(input).toHaveValue('1.25K');
    });

    it('onChange callback should be executed if the user presses ENTER key', async () => {
        let value = 1000;
        const mockOnChange = jest.fn((result) => {
            value = result;
        });

        const App = () => {
            return (
                <CustomNumberField
                    defaultValue={1}
                    value={value}
                    onChange={mockOnChange}
                    step={1}
                    maxValue={10000}
                    minValue={0}
                    isValueChangedAdHoc
                />
            );
        };

        render(<App />);

        const input = screen.getByRole('textbox');

        fireEvent.change(input, { target: { value: '' } });
        fireEvent.change(input, { target: { value: '5555' } });
        fireEvent.keyDown(input, { key: ' Enter', code: 13 });

        await waitFor(() => {
            expect(mockOnChange).toHaveBeenCalledWith(5555);
        });
    });
});
