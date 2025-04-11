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

import { fireEvent, screen, within } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { USER_ROLE } from '../../../../core/users/users.interface';
import {
    CONFIRM_PASSWORD_ERROR_MESSAGE,
    MISSING_REQUIRED_CHARACTERS_MESSAGE,
    PASSWORD_DOES_NOT_MEET_LENGTH_RULE,
} from '../../../../shared/utils';
import { getMockedWorkspaceIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { AddMemberPopup } from './add-member-popup.component';
import { CORRECT_PASS, INCORRECT_PASS, PASSWORD_WITH_MORE_THAN_200_CHARS } from './test-utils';

const mockedWorkspaceIdentifier = getMockedWorkspaceIdentifier({ workspaceId: 'testing-workspace' });

jest.mock('../../../../providers/workspaces-provider/workspaces-provider.component', () => ({
    useWorkspaces: jest.fn(() => ({ workspaceId: mockedWorkspaceIdentifier.workspaceId })),
}));

describe('Add member popup', () => {
    const userInput = {
        id: 'test@email.com',
        firstName: 'Test',
        lastName: 'Snow',
        email: 'test@email.com',
        password: 'dGVzdDEyMzQ=',
        roles: [USER_ROLE.WORKSPACE_CONTRIBUTOR],
        registered: true,
    };

    const getAllFields = () => {
        const emailField = screen.getByLabelText('Email address');
        const firstName = screen.getByLabelText('First name');
        const lastName = screen.getByLabelText('Last name');
        const passwordField = screen.getByLabelText('Password');
        const confirmField = screen.getByLabelText('Confirm password');
        const saveButton = screen.getByRole('button', { name: 'save add user' });

        return { emailField, firstName, lastName, passwordField, confirmField, saveButton };
    };

    const renderAddMember = async () => {
        render(
            <AddMemberPopup
                organizationId={mockedWorkspaceIdentifier.organizationId}
                workspaceId={mockedWorkspaceIdentifier.workspaceId}
            />
        );

        screen.getByRole('button', { name: 'Add user' }).click();
    };

    it('should render without error', async () => {
        await renderAddMember();

        expect(screen.getByTestId('add-user-title-id')).toHaveTextContent('Add user');
    });

    it('should display "Select a role"', async () => {
        await renderAddMember();

        const rolesPicker = screen.getByRole('button', { expanded: false });

        const defaultValue = within(rolesPicker).getByText('Select a role');
        expect(defaultValue).toBeInTheDocument();
    });

    it('allows an admin to add an admin', async () => {
        await renderAddMember();

        const rolesPicker = screen.getByRole('button', { expanded: false });

        await userEvent.selectOptions(
            screen.getByRole('combobox', { name: 'Role', hidden: true }),
            screen.getByRole('option', { name: USER_ROLE.WORKSPACE_ADMIN, hidden: true })
        );

        const defaultValue = within(rolesPicker).getByText(USER_ROLE.WORKSPACE_ADMIN);
        expect(defaultValue).toBeInTheDocument();
    });

    it('save button should be disabled initially', async () => {
        await renderAddMember();

        const saveButton = screen.getByText('Add').closest('button');

        expect(saveButton).toBeDisabled();
    });

    it('save button should be disabled when any of the fields is empty, enabled when all fields are filled', async () => {
        await renderAddMember();

        const {
            emailField,
            firstName: firstNameField,
            lastName: lastNameField,
            passwordField,
            confirmField,
            saveButton,
        } = getAllFields();
        const { email, firstName, lastName } = userInput;

        fireEvent.change(emailField, { target: { value: email } });
        expect(saveButton).toBeDisabled();

        fireEvent.change(firstNameField, { target: { value: firstName } });
        fireEvent.change(lastNameField, { target: { value: lastName } });
        expect(saveButton).toBeDisabled();

        await userEvent.selectOptions(
            screen.getByRole('combobox', { name: 'Role', hidden: true }),
            screen.getByRole('option', { name: USER_ROLE.WORKSPACE_CONTRIBUTOR, hidden: true })
        );

        expect(saveButton).toBeDisabled();

        fireEvent.change(passwordField, { target: { value: CORRECT_PASS } });
        expect(saveButton).toBeDisabled();

        fireEvent.change(confirmField, { target: { value: CORRECT_PASS } });

        expect(saveButton).toBeEnabled();
    });

    it('save button should be disabled when email is incorrect', async () => {
        await renderAddMember();

        const {
            emailField,
            firstName: firstNameField,
            lastName: lastNameField,
            passwordField,
            confirmField,
            saveButton,
        } = getAllFields();
        const { firstName, lastName } = userInput;

        fireEvent.change(emailField, { target: { value: firstName } });
        fireEvent.change(firstNameField, { target: { value: firstName } });
        fireEvent.change(lastNameField, { target: { value: lastName } });
        fireEvent.change(passwordField, { target: { value: CORRECT_PASS } });
        fireEvent.change(confirmField, { target: { value: CORRECT_PASS } });

        expect(saveButton).toBeDisabled();
    });

    it('should show the error message when passwords do not match', async () => {
        await renderAddMember();

        const {
            emailField,
            firstName: firstNameField,
            lastName: lastNameField,
            passwordField,
            confirmField,
            saveButton,
        } = getAllFields();
        const { email, firstName, lastName } = userInput;

        fireEvent.change(emailField, { target: { value: email } });
        fireEvent.change(firstNameField, { target: { value: firstName } });
        fireEvent.change(lastNameField, { target: { value: lastName } });
        fireEvent.change(passwordField, { target: { value: CORRECT_PASS } });
        fireEvent.change(confirmField, { target: { value: '4321Test' } });

        await userEvent.selectOptions(
            screen.getByRole('combobox', { name: 'Role', hidden: true }),
            screen.getByRole('option', { name: USER_ROLE.WORKSPACE_CONTRIBUTOR, hidden: true })
        );

        fireEvent.click(saveButton);

        expect(screen.getByText(CONFIRM_PASSWORD_ERROR_MESSAGE)).toBeInTheDocument();
    });

    it('save button should be disabled when password does not have capital letter or symbol', async () => {
        await renderAddMember();

        const {
            emailField,
            firstName: firstNameField,
            lastName: lastNameField,
            passwordField,
            confirmField,
            saveButton,
        } = getAllFields();
        const { email, firstName, lastName } = userInput;

        fireEvent.change(emailField, { target: { value: email } });
        expect(saveButton).toBeDisabled();

        fireEvent.change(firstNameField, { target: { value: firstName } });
        fireEvent.change(lastNameField, { target: { value: lastName } });
        expect(saveButton).toBeDisabled();

        await userEvent.selectOptions(
            screen.getByRole('combobox', { name: 'Role', hidden: true }),
            screen.getByRole('option', { name: USER_ROLE.WORKSPACE_CONTRIBUTOR, hidden: true })
        );

        fireEvent.change(passwordField, { target: { value: INCORRECT_PASS } });
        expect(saveButton).toBeDisabled();

        fireEvent.change(confirmField, { target: { value: INCORRECT_PASS } });

        fireEvent.click(saveButton);

        expect(screen.getByText(MISSING_REQUIRED_CHARACTERS_MESSAGE)).toBeInTheDocument();
    });

    it('error message should be shown and save button be disabled when password is longer than 200 characters', async () => {
        await renderAddMember();

        const {
            passwordField,
            emailField,
            firstName: firstNameField,
            lastName: lastNameField,
            confirmField,
            saveButton,
        } = getAllFields();
        const { email, firstName, lastName } = userInput;

        fireEvent.change(emailField, { target: { value: email } });
        fireEvent.change(firstNameField, { target: { value: firstName } });
        fireEvent.change(lastNameField, { target: { value: lastName } });

        fireEvent.change(passwordField, { target: { value: PASSWORD_WITH_MORE_THAN_200_CHARS } });

        expect(screen.getByText(PASSWORD_DOES_NOT_MEET_LENGTH_RULE)).toBeInTheDocument();

        fireEvent.change(confirmField, { target: { value: CORRECT_PASS } });

        expect(saveButton).toBeDisabled();
    });

    it('error message should be shown and save button be disabled when confirm password is longer than 200 characters', async () => {
        await renderAddMember();

        const {
            passwordField,
            emailField,
            firstName: firstNameField,
            lastName: lastNameField,
            confirmField,
            saveButton,
        } = getAllFields();
        const { email, firstName, lastName } = userInput;

        fireEvent.change(emailField, { target: { value: email } });

        fireEvent.change(firstNameField, { target: { value: firstName } });
        fireEvent.change(lastNameField, { target: { value: lastName } });

        fireEvent.change(passwordField, { target: { value: CORRECT_PASS } });

        fireEvent.change(confirmField, { target: { value: PASSWORD_WITH_MORE_THAN_200_CHARS } });

        expect(screen.getByText(PASSWORD_DOES_NOT_MEET_LENGTH_RULE)).toBeInTheDocument();

        expect(saveButton).toBeDisabled();
    });

    it('when user pastes password longer than 200 characters the previously typed password is not replaced', async () => {
        await renderAddMember();

        const { passwordField, emailField, firstName: firstNameField, lastName: lastNameField } = getAllFields();
        const { email, firstName, lastName } = userInput;

        fireEvent.change(emailField, { target: { value: email } });

        fireEvent.change(firstNameField, { target: { value: firstName } });
        fireEvent.change(lastNameField, { target: { value: lastName } });

        fireEvent.change(passwordField, { target: { value: CORRECT_PASS } });

        await userEvent.paste(PASSWORD_WITH_MORE_THAN_200_CHARS);

        expect(passwordField).toHaveValue(CORRECT_PASS);
    });

    it('when user pastes confirm password longer than 200 characters the previously typed confirm password is not replaced', async () => {
        await renderAddMember();

        const {
            passwordField,
            emailField,
            firstName: firstNameField,
            lastName: lastNameField,
            confirmField,
        } = getAllFields();
        const { email, firstName, lastName } = userInput;

        fireEvent.change(emailField, { target: { value: email } });

        fireEvent.change(firstNameField, { target: { value: firstName } });
        fireEvent.change(lastNameField, { target: { value: lastName } });

        fireEvent.change(passwordField, { target: { value: CORRECT_PASS } });
        fireEvent.change(confirmField, { target: { value: CORRECT_PASS } });

        await userEvent.paste(PASSWORD_WITH_MORE_THAN_200_CHARS);

        expect(confirmField).toHaveValue(CORRECT_PASS);
    });
});
