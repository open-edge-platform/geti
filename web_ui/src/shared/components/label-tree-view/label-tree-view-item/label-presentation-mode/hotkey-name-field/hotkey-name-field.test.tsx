// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../../../../../test-utils/required-providers-render';
import { HotkeyNameField } from './hotkey-name-field.component';

describe('Hotkey name field', () => {
    it('Error icon should be on the screen', async () => {
        const error = 'This is an error';

        render(<HotkeyNameField text={'test hotkey'} onChange={jest.fn()} error={error} />);

        fireEvent.click(screen.getByRole('link', { name: 'test hotkey' }));
        expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument();
    });

    it("Typing 'A' and then 'CTRL+F'", async () => {
        const onChangeMock = jest.fn();

        render(<HotkeyNameField text={'test hotkey'} onChange={onChangeMock} error={''} />);

        fireEvent.click(screen.getByRole('link', { name: 'test hotkey' }));
        fireEvent.keyDown(screen.getByRole('textbox'), { key: 'a' });
        fireEvent.keyUp(screen.getByRole('textbox'), { key: 'a' });

        expect(onChangeMock).toHaveBeenCalledWith('A');
    });

    it('Should be closable with empty and filled value', async () => {
        render(<HotkeyNameField text={'test hotkey'} onChange={jest.fn()} error={''} />);

        // Test with empty value
        fireEvent.click(screen.getByRole('link', { name: 'test hotkey' }));
        expect(screen.getByRole('textbox')).toBeInTheDocument();
        fireEvent.click(screen.getByTestId('hotkey-close-button'));
        expect(screen.queryByRole('textbox')).not.toBeInTheDocument();

        // Test with filled value
        fireEvent.click(screen.getByRole('link', { name: 'test hotkey' }));
        expect(screen.getByRole('textbox')).toBeInTheDocument();

        fireEvent.keyDown(screen.getByRole('textbox'), { key: 'a' });
        fireEvent.keyUp(screen.getByRole('textbox'), { key: 'a' });

        fireEvent.click(screen.getByTestId('hotkey-close-button'));
        expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    });
});
