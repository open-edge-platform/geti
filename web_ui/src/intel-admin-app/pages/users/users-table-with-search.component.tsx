// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, useState } from 'react';

import { Flex, View } from '@adobe/react-spectrum';
import { SearchField } from '@shared/components/search-field/search-field.component';

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
