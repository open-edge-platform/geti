// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { screen } from '@testing-library/react';

import { getMockedUser } from '../../../../../test-utils/mocked-items-factory/mocked-users';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { getFullNameFromUser } from '../utils';
import { UserNameCell } from './user-name-cell.component';

describe('UsernameCell', () => {
    const mockedUser = getMockedUser({ id: 'user-id' });
    const fullName = getFullNameFromUser(mockedUser);

    it('Check if organization admin is marked in the table', async () => {
        render(
            <UserNameCell
                dataKey={mockedUser.id}
                id={mockedUser.id}
                userPhoto={null}
                fullName={fullName}
                email={mockedUser.email}
                isOrgAdmin
                cellData={fullName}
            />
        );

        expect(screen.getByTestId('organization-admin-indicator')).toBeInTheDocument();
    });

    it('Check if not organization admin is not marked in the table', async () => {
        render(
            <UserNameCell
                dataKey={mockedUser.id}
                id={mockedUser.id}
                userPhoto={null}
                fullName={fullName}
                email={mockedUser.email}
                isOrgAdmin={false}
                cellData={fullName}
            />
        );

        expect(screen.queryByTestId('organization-admin-indicator')).not.toBeInTheDocument();
    });
});
