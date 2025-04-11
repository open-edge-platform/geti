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
