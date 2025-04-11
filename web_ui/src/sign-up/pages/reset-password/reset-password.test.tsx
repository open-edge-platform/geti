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

import { screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import dayjs from 'dayjs';
import { jwtDecode } from 'jwt-decode';

import {
    CORRECT_PASS,
    INCORRECT_PASS,
    PASSWORD_WITH_MORE_THAN_200_CHARS,
} from '../../../pages/user-management/users/add-member-popup/test-utils';
import {
    CONFIRM_PASSWORD_ERROR_MESSAGE,
    MISSING_REQUIRED_CHARACTERS_MESSAGE,
    PASSWORD_DOES_NOT_MEET_LENGTH_RULE,
} from '../../../shared/utils';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { ResetPassword } from './reset-password.component';

const mockToken = 'cool-token';
const mockToday = dayjs();
const mockMail = 'test@gmail.com';

jest.mock('jwt-decode', () => ({
    jwtDecode: jest.fn(() => ({ exp: mockToday.add(1, 'day').unix(), mail: mockMail })),
}));

const renderResetPassword = (
    { initialEntries }: { initialEntries?: string[] } = { initialEntries: [`?token=${mockToken}`] }
) => {
    render(<ResetPassword />, { initialEntries });
};

describe('Reset password', () => {
    const emailStoredInToken = 'test@gmail.com';

    afterEach(() => {
        jest.clearAllMocks();
    });

    it("User's email should be shown", () => {
        renderResetPassword();

        expect(screen.getByTestId('for-email-id')).toHaveTextContent(emailStoredInToken);
    });

    it('Submit new password button should be disabled when password fields are empty', () => {
        renderResetPassword(undefined);

        expect(screen.getByRole('button', { name: /submit new password/i })).toBeDisabled();
    });

    it('Submit new password button should be enabled when password fields are not empty', async () => {
        renderResetPassword(undefined);

        await userEvent.type(screen.getByLabelText('New password'), CORRECT_PASS);

        await userEvent.type(screen.getByLabelText('Confirm new password'), CORRECT_PASS);

        expect(screen.getByRole('button', { name: /submit new password/i })).toBeEnabled();
    });

    it('Submit new password button should be disabled when any password does not meet reqs', async () => {
        renderResetPassword(undefined);

        const submitBtn = screen.getByRole('button', { name: /submit new password/i });

        await userEvent.type(screen.getByLabelText('New password'), INCORRECT_PASS);

        await userEvent.type(screen.getByLabelText('Confirm new password'), CORRECT_PASS);

        await userEvent.click(submitBtn);

        expect(submitBtn).toBeDisabled();
    });

    it('Error should be shown when password does not meet reqs', async () => {
        renderResetPassword(undefined);

        await userEvent.type(screen.getByLabelText('New password'), INCORRECT_PASS);

        await userEvent.type(screen.getByLabelText('Confirm new password'), CORRECT_PASS);

        await userEvent.click(screen.getByRole('button', { name: /submit new password/i }));

        expect(screen.getByTestId('new-password-error-msg')).toHaveTextContent(MISSING_REQUIRED_CHARACTERS_MESSAGE);
    });

    it('Error should be shown when passwords do not match', async () => {
        renderResetPassword(undefined);

        await userEvent.type(screen.getByLabelText('New password'), CORRECT_PASS);

        await userEvent.type(screen.getByLabelText('Confirm new password'), CORRECT_PASS + '5');

        await userEvent.click(screen.getByRole('button', { name: /submit new password/i }));

        expect(screen.getByTestId('confirm-new-password-error-msg')).toHaveTextContent(CONFIRM_PASSWORD_ERROR_MESSAGE);
    });

    it('Error message should be shown and submit button be disabled when confirm password is longer than 200 characters', async () => {
        renderResetPassword(undefined);

        await userEvent.type(screen.getByLabelText('New password'), PASSWORD_WITH_MORE_THAN_200_CHARS);

        expect(screen.getByRole('button', { name: /submit new password/i })).toBeDisabled();
        expect(screen.getByText(PASSWORD_DOES_NOT_MEET_LENGTH_RULE)).toBeInTheDocument();
    });

    it('when user pastes password longer than 200 characters the previously typed password is not replaced', async () => {
        renderResetPassword(undefined);

        const newPassword = screen.getByLabelText('New password');

        await userEvent.type(newPassword, CORRECT_PASS);
        await userEvent.paste(PASSWORD_WITH_MORE_THAN_200_CHARS);

        expect(newPassword).toHaveValue(CORRECT_PASS);
    });

    it('when user pastes confirm password longer than 200 characters the previously typed confirm password is not replaced', async () => {
        renderResetPassword(undefined);

        const confirmPassword = screen.getByLabelText('Confirm new password');

        await userEvent.type(confirmPassword, CORRECT_PASS);
        await userEvent.paste(PASSWORD_WITH_MORE_THAN_200_CHARS);

        expect(confirmPassword).toHaveValue(CORRECT_PASS);
    });

    it('should display an error message when the token is expired', async () => {
        jest.mocked(jwtDecode).mockReturnValue({ exp: mockToday.subtract(1, 'day').unix(), mail: mockMail });

        renderResetPassword(undefined);

        expect(await screen.findByRole('alert')).toBeInTheDocument();
        expect(screen.getByRole('heading', { name: 'Your invitation link has expired' })).toBeInTheDocument();
    });

    it('should display an error message when the token is not present in the url', async () => {
        renderResetPassword({ initialEntries: undefined });

        expect(await screen.findByRole('alert')).toBeInTheDocument();
        expect(
            screen.getByRole('heading', { name: 'Invitation token is required for further actions' })
        ).toBeInTheDocument();
    });
});
