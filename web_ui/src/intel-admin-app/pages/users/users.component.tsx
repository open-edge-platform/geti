// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { MOCKED_USERS } from './mocked-user';
import { UsersTableWithSearch } from './users-table-with-search.component';

export const Users: FC = () => {
    const useUsersQuery = () => {
        return {
            data: MOCKED_USERS,
        };
    };

    return <UsersTableWithSearch useUsersQuery={useUsersQuery} />;
};
