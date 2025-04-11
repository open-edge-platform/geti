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
import { userEvent } from '@testing-library/user-event';

import { providersRender as render } from '../../../../../../test-utils/required-providers-render';
import { HotkeyEditionField } from './hotkey-edition-field.component';

describe('Hotkey edition field', () => {
    const onChangeMock = jest.fn();

    const renderApp = (value = 'control+a'): HTMLElement => {
        render(<HotkeyEditionField value={value} onChange={onChangeMock} aria-label={'test hotkey edition field'} />);

        const hotkeyField = screen.getByRole('textbox', { name: 'test hotkey edition field' });
        expect(hotkeyField).toHaveValue(value);
        fireEvent.click(hotkeyField);

        return hotkeyField;
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('check if edited hotkey has visible new value', async () => {
        renderApp();

        await userEvent.keyboard('{s>}d{/s}');
        expect(onChangeMock).toHaveBeenCalledWith('S+D');
    });

    it('check if hotkey is limited to 2 keys', async () => {
        renderApp();

        await userEvent.keyboard('{q>}{e>}r{/q}{/e}');
        expect(onChangeMock).toHaveBeenCalledWith('E+R');
    });

    it('does not add multiple modifiers', async () => {
        renderApp();

        await userEvent.keyboard('{shift}{ctrl/}');
        expect(onChangeMock).toHaveBeenCalledWith('SHIFT');

        await userEvent.keyboard('{Alt}{Meta/}');
        expect(onChangeMock).toHaveBeenCalledWith('ALT');
    });

    it('add "Shift+number" as numerical value', async () => {
        renderApp();

        await userEvent.keyboard('{Shift>}1{/Shift}');
        expect(onChangeMock).toHaveBeenCalledWith('SHIFT+1');

        await userEvent.keyboard('{Shift>}9{/Shift}');
        expect(onChangeMock).toHaveBeenCalledWith('SHIFT+9');
    });
});
