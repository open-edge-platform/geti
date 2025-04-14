// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor } from '@testing-library/react';
import dayjs from 'dayjs';
import { jwtDecode } from 'jwt-decode';

import { createInMemoryUsersService } from '../../../core/users/services/in-memory-users-service';
import { encodeToBase64 } from '../../../shared/utils';
import { providersRender } from '../../../test-utils/required-providers-render';
import { Registration } from './registration.component';

const mockToken = 'cool-token';
const mockToday = dayjs();
const mockMail = 'test@gmail.com';

jest.mock('jwt-decode', () => ({
    jwtDecode: jest.fn(() => ({ exp: mockToday.add(1, 'day').unix(), mail: mockMail })),
}));

const mockRegisterUser = jest.fn();

const renderComponent = (
    { initialEntries }: { initialEntries: string[] | undefined } = {
        initialEntries: [`?token=${mockToken}`],
    }
) => {
    const usersService = createInMemoryUsersService();

    usersService.registerMember = mockRegisterUser;

    providersRender(<Registration />, { services: { usersService }, initialEntries });
};

describe('Registration', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    it('renders the form correctly', async () => {
        renderComponent();

        expect(screen.getByLabelText('First name')).toBeInTheDocument();
        expect(screen.getByLabelText('Last name')).toBeInTheDocument();
        expect(screen.getByLabelText('Password')).toBeInTheDocument();
        expect(screen.getByLabelText('Confirm password')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Sign up' })).toBeInTheDocument();
    });

    it('has the sign up button disabled until all the fields are filled', async () => {
        renderComponent();

        expect(screen.getByRole('button', { name: 'Sign up' })).toBeDisabled();

        fireEvent.input(screen.getByLabelText('First name'), { target: { value: 'John' } });
        expect(screen.getByRole('button', { name: 'Sign up' })).toBeDisabled();

        fireEvent.input(screen.getByLabelText('Last name'), { target: { value: 'Endurance' } });
        expect(screen.getByRole('button', { name: 'Sign up' })).toBeDisabled();

        fireEvent.input(screen.getByLabelText('Password'), { target: { value: '@SCAdmin1' } });
        expect(screen.getByRole('button', { name: 'Sign up' })).toBeDisabled();

        fireEvent.input(screen.getByLabelText('Confirm password'), { target: { value: '@SCAdmin1' } });
        expect(screen.getByRole('button', { name: 'Sign up' })).toBeEnabled();
    });

    it('sends the correct payload and redirects to the homepage', async () => {
        renderComponent();

        fireEvent.input(screen.getByLabelText('First name'), { target: { value: 'John' } });
        fireEvent.input(screen.getByLabelText('Last name'), { target: { value: 'Endurance' } });
        fireEvent.input(screen.getByLabelText('Password'), { target: { value: '@SCAdmin1' } });
        fireEvent.input(screen.getByLabelText('Confirm password'), { target: { value: '@SCAdmin1' } });

        expect(screen.getByRole('button', { name: 'Sign up' })).toBeEnabled();

        fireEvent.click(screen.getByRole('button', { name: 'Sign up' }));

        await waitFor(() => {
            expect(mockRegisterUser).toHaveBeenCalledWith({
                token: mockToken,
                first_name: 'John',
                second_name: 'Endurance',
                password: encodeToBase64('@SCAdmin1'),
            });
        });

        expect(window.location.href).toEqual('http://localhost/');
    });

    it.each(['S1s', 'ssssssssss', 'S1ss'.repeat(51)])('Passowrd "%s" should show a validation error', (password) => {
        renderComponent();

        fireEvent.input(screen.getByLabelText('First name'), { target: { value: 'John' } });
        fireEvent.input(screen.getByLabelText('Last name'), { target: { value: 'Endurance' } });
        fireEvent.input(screen.getByLabelText('Password'), { target: { value: password } });
        fireEvent.input(screen.getByLabelText('Confirm password'), { target: { value: password } });

        expect(screen.getByRole('button', { name: 'Sign up' })).toBeEnabled();

        fireEvent.click(screen.getByRole('button', { name: 'Sign up' }));

        expect(screen.getByTestId('password-error-msg')).toBeVisible();
    });

    it('should show an error alert when token is expired', async () => {
        jest.mocked(jwtDecode).mockReturnValue({ exp: mockToday.subtract(1, 'day').unix(), mail: mockMail });
        renderComponent();

        expect(await screen.findByRole('alert')).toBeInTheDocument();
        expect(screen.getByRole('heading', { name: 'Your invitation link has expired' })).toBeInTheDocument();
    });

    it('should show an error alert when token is not present in the url', async () => {
        renderComponent({ initialEntries: undefined });

        expect(await screen.findByRole('alert')).toBeInTheDocument();
        expect(
            screen.getByRole('heading', { name: 'Invitation token is required for further actions' })
        ).toBeInTheDocument();
    });
});
