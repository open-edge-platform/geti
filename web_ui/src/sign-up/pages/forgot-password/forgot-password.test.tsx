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

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { providersRender as render } from '../../../test-utils/required-providers-render';
import { ForgotPassword } from './forgot-password.component';

describe('Forgot password', () => {
    it('Reset button should be disabled when there is no email', async () => {
        render(<ForgotPassword />);

        expect(screen.getByRole('button', { name: 'Reset' })).toBeDisabled();
    });

    it('Reset button should be disabled when email is incorrect', async () => {
        render(<ForgotPassword />);

        fireEvent.change(screen.getByRole('textbox'), { target: { value: 'incorrect_email@' } });

        expect(screen.getByRole('button', { name: 'Reset' })).toBeDisabled();
    });

    it('Reset button should be enabled when email is correct', async () => {
        render(<ForgotPassword />);

        fireEvent.change(screen.getByRole('textbox'), { target: { value: 'correct_email@gmail.com' } });

        expect(screen.getByRole('button', { name: 'Reset' })).toBeEnabled();
    });

    it('Password recovery message should be shown', async () => {
        render(<ForgotPassword />);

        fireEvent.change(screen.getByRole('textbox'), { target: { value: 'correct_email@gmail.com' } });
        fireEvent.click(screen.getByRole('button', { name: 'Reset' }));

        await waitFor(() => {
            expect(screen.getByTestId('recovery-msg-id')).toHaveTextContent(
                'A message has been sent to your email with further instructions.'
            );
        });
    });
});
