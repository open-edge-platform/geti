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
