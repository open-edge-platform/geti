// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FC } from 'react';

import { Flex, View } from '@adobe/react-spectrum';

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
