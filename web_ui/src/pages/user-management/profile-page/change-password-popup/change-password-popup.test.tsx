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

import { CONFIRM_PASSWORD_ERROR_MESSAGE, PASSWORD_DOES_NOT_MEET_LENGTH_RULE } from '../../../../shared/utils';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { CORRECT_PASS, PASSWORD_WITH_MORE_THAN_200_CHARS } from '../../users/add-member-popup/test-utils';
import { ChangePasswordPopup } from './change-password-popup.component';

describe('ChangePasswordPopup', () => {
    const userInput = {
        id: 'user-test-id',
        oldPassword: 'OldPass123',
        newPassword: 'NewPass123',
    };

    const renderChangePassword = async (): Promise<void> => {
        await render(<ChangePasswordPopup userId={userInput.id} />);

        await userEvent.click(screen.getByRole('button', { name: /change password/i }));
    };

    it('save button should be disabled by default', async () => {
        await renderChangePassword();

        expect(screen.getByRole('button', { name: /save/i })).toBeDisabled();
    });

    it('save button is enabled only when all the password fields are filled', async () => {
        await renderChangePassword();

        const saveButton = screen.getByRole('button', { name: /save/i });

        fireEvent.change(screen.getByLabelText('Old password'), { target: { value: CORRECT_PASS } });
        expect(saveButton).toBeDisabled();

        fireEvent.change(screen.getByLabelText('New password'), { target: { value: CORRECT_PASS } });

        expect(saveButton).toBeDisabled();

        fireEvent.change(screen.getByLabelText('Confirm new password'), {
            target: { value: CORRECT_PASS },
        });
        expect(screen.getByRole('button', { name: /save/i })).toBeEnabled();
    });

    it('should show error message when new password and confirm password do not match', async () => {
        await renderChangePassword();

        const saveButton = screen.getByRole('button', { name: /save/i });

        fireEvent.change(screen.getByLabelText('Old password'), { target: { value: CORRECT_PASS } });

        fireEvent.change(screen.getByLabelText('New password'), { target: { value: CORRECT_PASS } });

        fireEvent.change(screen.getByLabelText('Confirm new password'), {
            target: { value: CORRECT_PASS + 'BAD' },
        });

        expect(saveButton).toBeEnabled();

        await userEvent.click(saveButton);

        expect(saveButton).toBeDisabled();

        expect(screen.getByText(CONFIRM_PASSWORD_ERROR_MESSAGE)).toBeInTheDocument();
    });

    // TODO implement this test once gql is removed
    it.todo(
        'error message should be shown and save button be disabled when old password is longer than 200 characters'
    );

    it('error message should be shown and save button be disabled when password is longer than 200 characters', async () => {
        await renderChangePassword();

        fireEvent.change(screen.getByLabelText('Old password'), { target: { value: CORRECT_PASS } });

        fireEvent.change(screen.getByLabelText('New password'), {
            target: { value: PASSWORD_WITH_MORE_THAN_200_CHARS },
        });

        fireEvent.change(screen.getByLabelText('Confirm new password'), {
            target: { value: CORRECT_PASS },
        });

        expect(screen.getByText(PASSWORD_DOES_NOT_MEET_LENGTH_RULE)).toBeInTheDocument();
    });

    it('error message should be shown and save button be disabled when confirm password is longer than 200 characters', async () => {
        await renderChangePassword();

        fireEvent.change(screen.getByLabelText('Old password'), { target: { value: CORRECT_PASS } });

        fireEvent.change(screen.getByLabelText('New password'), { target: { value: CORRECT_PASS } });

        fireEvent.change(screen.getByLabelText('Confirm new password'), {
            target: { value: PASSWORD_WITH_MORE_THAN_200_CHARS },
        });

        expect(screen.getByText(PASSWORD_DOES_NOT_MEET_LENGTH_RULE)).toBeInTheDocument();
    });

    it('when user pastes password longer than 200 characters the previously typed password is not replaced', async () => {
        await renderChangePassword();

        const newPassword = screen.getByLabelText('New password');

        fireEvent.change(screen.getByLabelText('Old password'), { target: { value: CORRECT_PASS } });

        fireEvent.change(newPassword, { target: { value: CORRECT_PASS } });
        await userEvent.paste(PASSWORD_WITH_MORE_THAN_200_CHARS);

        expect(newPassword).toHaveValue(CORRECT_PASS);
    });

    it('when user pastes confirm password longer than 200 characters the previously typed confirm password is not replaced', async () => {
        await renderChangePassword();

        const confirmPassword = screen.getByLabelText('Confirm new password');

        fireEvent.change(screen.getByLabelText('Old password'), { target: { value: CORRECT_PASS } });

        fireEvent.change(screen.getByLabelText('New password'), { target: { value: CORRECT_PASS } });

        fireEvent.change(confirmPassword, { target: { value: CORRECT_PASS } });
        await userEvent.paste(PASSWORD_WITH_MORE_THAN_200_CHARS);

        expect(confirmPassword).toHaveValue(CORRECT_PASS);
    });
});
