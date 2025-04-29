// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
