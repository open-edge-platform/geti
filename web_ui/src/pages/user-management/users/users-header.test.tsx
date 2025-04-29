// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { providersRender as render } from '../../../test-utils/required-providers-render';
import { UsersHeader } from './users-header.component';

describe('UsersHeader', () => {
    it('Check all users header elements', async () => {
        render(
            <UsersHeader
                totalMatchedCount={2}
                totalCount={3}
                hasFilterOptions={false}
                setUsersQueryParams={jest.fn()}
            />
        );

        expect(screen.getByTestId('users-header-search-field')).toBeInTheDocument();
        expect(screen.getByTestId('users-header-role-picker')).toBeInTheDocument();
        expect(screen.getByTestId('users-header-users-count')).toBeInTheDocument();
    });
});
