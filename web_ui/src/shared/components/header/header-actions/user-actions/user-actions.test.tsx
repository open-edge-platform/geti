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

import { createInMemoryUsersService } from '../../../../../core/users/services/in-memory-users-service';
import { MediaUploadProvider } from '../../../../../providers/media-upload-provider/media-upload-provider.component';
import { getMockedUser } from '../../../../../test-utils/mocked-items-factory/mocked-users';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { UserActions } from './user-actions.component';

describe('UserActions', () => {
    it('Check if actions are available: User summary, Profile and Sign out ', async () => {
        const usersService = createInMemoryUsersService();
        const mockedUser = getMockedUser({ email: 'test@mail.com' });
        usersService.getActiveUser = jest.fn(async () => mockedUser);

        render(
            <MediaUploadProvider>
                <UserActions isDarkMode={false} />
            </MediaUploadProvider>,
            { services: { usersService } }
        );

        fireEvent.click(await screen.findByRole('button', { name: 'User actions' }));

        expect(screen.getByTestId('user-summary-id')).toBeInTheDocument();
        expect(
            screen.getByText(`${mockedUser.firstName} ${mockedUser.lastName}`, { exact: false })
        ).toBeInTheDocument();
        expect(screen.getByText(mockedUser.email)).toBeInTheDocument();

        expect(screen.getAllByRole('menuitem')).toHaveLength(2);
        expect(screen.getByRole('menuitem', { name: 'Sign out' })).toBeInTheDocument();
    });
});
