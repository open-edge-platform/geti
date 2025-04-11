// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen } from '@testing-library/react';

import { createInMemoryCreditsService } from '../../../../core/credits/services/in-memory-credits-service';
import { paths } from '../../../../core/services/routes';
import { createInMemoryUsersService } from '../../../../core/users/services/in-memory-users-service';
import {
    getMockedOrganizationAdminUser,
    getMockedUser,
} from '../../../../test-utils/mocked-items-factory/mocked-users';
import { projectRender as render } from '../../../../test-utils/project-provider-render';
import { CreditBalanceStatus } from './credit-balance-status.component';
import { CREDIT_LOW_LIMIT } from './util';

jest.mock('../../../utils', () => ({
    ...jest.requireActual('../../../utils'),
    openNewTab: jest.fn(),
}));

const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockedNavigate,
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace-id',
    }),
}));

const renderApp = async ({
    isAdmin = false,
    creditsIncoming,
    creditsAvailable,
}: {
    isAdmin?: boolean;
    creditsIncoming: number;
    creditsAvailable: number;
}) => {
    const usersService = createInMemoryUsersService();
    const creditsService = createInMemoryCreditsService();
    creditsService.getOrganizationBalance = () =>
        Promise.resolve({ incoming: creditsIncoming, available: creditsAvailable, blocked: 0 });

    usersService.getActiveUser = async (_organizationId) =>
        isAdmin ? getMockedOrganizationAdminUser() : getMockedUser();

    return render(<CreditBalanceStatus isDarkMode={true} />, { services: { creditsService, usersService } });
};

describe('CreditBalanceStatus', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('credit exhausted', async () => {
        await renderApp({ creditsAvailable: 0, creditsIncoming: 100 });

        fireEvent.click(await screen.findByRole('button', { name: 'credit balance status' }));

        expect(screen.getByTestId('low-exhausted-warning')).toHaveTextContent('Exhausted');
    });

    it('credit running out', async () => {
        await renderApp({ creditsAvailable: CREDIT_LOW_LIMIT - 1, creditsIncoming: 100 });

        fireEvent.click(await screen.findByRole('button', { name: 'credit balance status' }));

        expect(screen.getByTestId('low-exhausted-warning')).toHaveTextContent('Running out');
    });

    it('"use details" is visible for admin user', async () => {
        await renderApp({ isAdmin: true, creditsAvailable: 100, creditsIncoming: 100 });

        fireEvent.click(await screen.findByRole('button', { name: 'credit balance status' }));

        fireEvent.click(await screen.findByRole('button', { name: /see usage details/i }));

        expect(mockedNavigate).toHaveBeenCalledWith(paths.account.usage({ organizationId: 'organization-id' }));
        expect(screen.queryByTestId('low-exhausted-warning')).not.toBeInTheDocument();
    });

    it('"use details" is not visible to contributors', async () => {
        await renderApp({ isAdmin: false, creditsAvailable: 100, creditsIncoming: 100 });

        fireEvent.click(await screen.findByRole('button', { name: 'credit balance status' }));

        expect(await screen.findByText('Credits remaining')).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /see usage details/i })).not.toBeInTheDocument();
    });
});
