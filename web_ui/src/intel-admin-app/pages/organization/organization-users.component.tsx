// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Flex, View } from '@geti/ui';

import { Header } from '../../shared/components/header/header.component';
import { MOCKED_USERS } from '../users/mocked-user';
import { UsersTableWithSearch } from '../users/users-table-with-search.component';

export const OrganizationUsers: FC = () => {
    const useUsersQuery = () => {
        return {
            data: [...MOCKED_USERS, ...MOCKED_USERS, ...MOCKED_USERS, ...MOCKED_USERS].map((us, i) => ({
                ...us,
                id: `${us.id}-${i}`,
            })),
        };
    };

    return (
        <Flex direction={'column'} height={'100%'}>
            <Header title={'Users'} />
            <View flex={1} overflow={'hidden'}>
                <UsersTableWithSearch useUsersQuery={useUsersQuery} />
            </View>
        </Flex>
    );
};
