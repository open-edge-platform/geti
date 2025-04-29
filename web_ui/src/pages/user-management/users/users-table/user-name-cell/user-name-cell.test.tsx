// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
