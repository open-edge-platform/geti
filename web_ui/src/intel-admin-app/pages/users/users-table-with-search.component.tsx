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

import { FC, useState } from 'react';

import { Flex, View } from '@adobe/react-spectrum';

import { SearchField } from '../../../shared/components/search-field/search-field.component';
import { EntitiesCounter } from '../../shared/components/entities-counter/entities-counter.component';
import { User } from './mocked-user';
import { UsersTable } from './users-table.component';

interface UsersTableWithSearchProps {
    useUsersQuery: () => { data: User[] };
}

export const UsersTableWithSearch: FC<UsersTableWithSearchProps> = ({ useUsersQuery }) => {
    const [searchPhrase, setSearchPhrase] = useState<string>('');
    const { data: users } = useUsersQuery();

    const totalCount = users.length;
    const totalMatchedCount = users.length;
    const hasFilters = false;

    return (
        <Flex direction={'column'} height={'100%'} gap={'size-300'}>
            <Flex alignItems={'center'} gap={'size-200'}>
                <SearchField
                    placeholder={'Search by name or email'}
                    value={searchPhrase}
                    onChange={setSearchPhrase}
                    width={'size-4600'}
                />
                {totalCount > 0 && (
                    <EntitiesCounter
                        totalMatchedCount={totalMatchedCount}
                        totalCount={totalCount}
                        hasFilters={hasFilters}
                        entity={'user'}
                    />
                )}
            </Flex>

            <View flex={1} overflow={'hidden'}>
                <UsersTable users={users} />
            </View>
        </Flex>
    );
};
