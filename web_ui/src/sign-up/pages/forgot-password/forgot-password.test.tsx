// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
