// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
// import { fireEvent } from '@testing-library/react';

import { fireEvent, screen, within } from '@testing-library/react';

import { AccountStatus } from '../../../core/organizations/organizations.interface';
import { getMockedOrganization } from '../../../test-utils/mocked-items-factory/mocked-organization';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { OrganizationOverview } from './organization-overview.component';

let mockedOrganization = getMockedOrganization();
const mockedMutateOrganization = jest.fn((updatedOrganization) => {
    mockedOrganization = updatedOrganization;
});
jest.mock('./hooks/organization.hook', () => ({
    useOrganization: () => ({
        organization: mockedOrganization,
        updateOrganization: {
            mutate: mockedMutateOrganization,
        },
        isLoading: false,
    }),
}));

describe('OrganizationOverview', () => {
    beforeEach(() => {
        mockedOrganization = getMockedOrganization();
        mockedMutateOrganization.mockClear();
    });

    test('renders organization details', () => {
        render(<OrganizationOverview />, {
            featureFlags: {
                FEATURE_FLAG_CREDIT_SYSTEM: true,
            },
        });

        expect(screen.getByText('Overview')).toBeInTheDocument();
        expect(screen.getByTestId('organization-overview-id-input')).toHaveValue(mockedOrganization.id);
        expect(screen.getByTestId('organization-overview-email-input')).toHaveValue(mockedOrganization.admins[0].email);
        expect(screen.getByTestId('organization-overview-name-input')).toHaveValue(mockedOrganization.name);
        expect(screen.getByTestId('organization-overview-status-input')).toHaveValue(mockedOrganization.status);
    });

    test('updates organization name on form submit', () => {
        render(<OrganizationOverview />, {
            featureFlags: {
                FEATURE_FLAG_CREDIT_SYSTEM: true,
            },
        });

        const nameInput = screen.getByTestId('organization-overview-name-input');
        fireEvent.change(nameInput, { target: { value: 'New Organization Name' } });
        const saveButton = screen.getByTestId('organization-overview-save-button');
        fireEvent.click(saveButton);

        expect(mockedMutateOrganization).toHaveBeenCalledWith({
            ...mockedOrganization,
            name: 'New Organization Name',
        });
    });

    test('triggers delete confirmation dialog', () => {
        render(<OrganizationOverview />, {
            featureFlags: {
                FEATURE_FLAG_CREDIT_SYSTEM: true,
            },
        });

        const deleteButton = screen.getByRole('button', { name: /Delete/i });
        fireEvent.click(deleteButton);

        expect(screen.getByTestId('modal')).toBeVisible();

        const confirmButton = within(screen.getByTestId('modal')).getByRole('button', { name: /Delete/i });
        fireEvent.click(confirmButton);

        expect(mockedMutateOrganization).toHaveBeenCalledWith({
            ...mockedOrganization,
            status: AccountStatus.DELETED,
        });
        expect(screen.queryByRole('button', { name: 'Delete' })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'Suspend' })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'Activate' })).not.toBeInTheDocument();
        expect(screen.getByLabelText('Status')).toHaveValue(AccountStatus.DELETED);
    });

    test('triggers suspend/activate buttons', async () => {
        const { rerender } = render(<OrganizationOverview />, {
            featureFlags: {
                FEATURE_FLAG_CREDIT_SYSTEM: true,
            },
        });

        const suspendButton = screen.getByRole('button', { name: /Suspend/i });

        fireEvent.click(suspendButton);

        expect(mockedMutateOrganization).toHaveBeenCalledWith({
            ...mockedOrganization,
            status: AccountStatus.SUSPENDED,
        });

        // React don't know that the organization status has changed, so we need to rerender the component
        rerender(<OrganizationOverview />);
        expect(screen.getByLabelText('Status')).toHaveValue(AccountStatus.SUSPENDED);
        expect(screen.queryByRole('button', { name: 'Suspend' })).not.toBeInTheDocument();

        const activateButton = screen.getByRole('button', { name: 'Activate' });
        fireEvent.click(activateButton);

        expect(mockedMutateOrganization).toHaveBeenCalledWith({
            ...mockedOrganization,
            status: AccountStatus.ACTIVATED,
        });
        rerender(<OrganizationOverview />);
        expect(screen.getByLabelText('Status')).toHaveValue(AccountStatus.ACTIVATED);
        expect(screen.queryByRole('button', { name: 'Activate' })).not.toBeInTheDocument();
    });

    test('Displays request access reason when FEATURE_FLAG_REQ_ACCESS enabled', () => {
        const requestAccessReason = 'Geti is great';
        mockedOrganization = getMockedOrganization({ requestAccessReason });

        render(<OrganizationOverview />, {
            featureFlags: {
                FEATURE_FLAG_CREDIT_SYSTEM: true,
                FEATURE_FLAG_REQ_ACCESS: true,
            },
        });

        expect(screen.getByRole('textbox', { name: /use case of using intel® geti™/i })).toHaveValue(
            requestAccessReason
        );
    });

    test('Does not display request access reason when FEATURE_FLAG_REQ_ACCESS enabled and reason is empty', () => {
        const requestAccessReason = '';
        mockedOrganization = getMockedOrganization({ requestAccessReason });

        render(<OrganizationOverview />, {
            featureFlags: {
                FEATURE_FLAG_CREDIT_SYSTEM: true,
                FEATURE_FLAG_REQ_ACCESS: true,
            },
        });

        expect(screen.queryByRole('textbox', { name: /use case of using intel® geti™/i })).not.toBeInTheDocument();
    });
});
