// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { createInMemoryUsersService } from '../../../core/users/services/in-memory-users-service';
import { MediaUploadProvider } from '../../../providers/media-upload-provider/media-upload-provider.component';
import { getMockedUser } from '../../../test-utils/mocked-items-factory/mocked-users';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { ProfilePage } from './profile-page.component';

jest.mock('../../../hooks/use-history-block/use-history-block.hook', () => ({
    useHistoryBlock: () => {
        return [false, jest.fn(), jest.fn()];
    },
}));

describe('Profile Page', () => {
    const firstName = 'Admin';
    const lastName = 'Adminowy';
    const email = 'admin@example.com';

    const usersService = createInMemoryUsersService();
    const activeUser = getMockedUser({ firstName, lastName, email });
    usersService.getActiveUser = async () => Promise.resolve(activeUser);

    const renderProfilePage = async (isSaaSEnv = false) => {
        return await render(
            <MediaUploadProvider>
                <ProfilePage activeUser={activeUser} organizationId={'organization-id'} isSaaSEnv={isSaaSEnv} />
            </MediaUploadProvider>,
            { services: { usersService } }
        );
    };

    it('First name, last name and email should be displayed properly', async () => {
        await renderProfilePage();

        const firstNameField = screen.getByLabelText('First name');
        const lastNameField = screen.getByLabelText('Last name');
        const emailField = screen.getByLabelText('Email address');
        expect(firstNameField).toHaveValue(firstName);
        expect(lastNameField).toHaveValue(lastName);
        expect(emailField).toHaveValue(email);
    });

    it('In SaaS application the "save" button should not be visible', async () => {
        await renderProfilePage(true);

        expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();
    });

    it('In SaaS application user should not be able to edit his data', async () => {
        await renderProfilePage(true);

        const fullNamePanel = screen.getByTestId('display-user-full-name');
        expect(fullNamePanel).toHaveValue('Admin Adminowy');
    });
});
