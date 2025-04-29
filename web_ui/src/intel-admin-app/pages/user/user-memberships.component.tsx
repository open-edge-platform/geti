// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, useState } from 'react';

import { Flex, View } from '@adobe/react-spectrum';

import { SearchField } from '../../../shared/components/search-field/search-field.component';
import { EntitiesCounter } from '../../shared/components/entities-counter/entities-counter.component';
import { Header } from '../../shared/components/header/header.component';
import {
    OrganizationsStatusesPicker,
    STATUSES,
    type OrganizationsStatusName,
} from '../organizations/organizations-statuses-picker.component';
import { MOCKED_USERS } from '../users/mocked-user';
import { MembershipsTable } from './memberships-table.component';
import { MOCKED_MEMBERSHIPS } from './mocked-memberships';

const [user] = MOCKED_USERS;

const UserMembershipsMainContent: FC = () => {
    const [searchPhrase, setSearchPhrase] = useState<string>('');
    const [selectedOrgStatus, setSelectedOrgStatus] = useState<OrganizationsStatusName>(STATUSES[0].name);

    const totalCount = MOCKED_MEMBERSHIPS.length;
    const totalMatchedCount = MOCKED_MEMBERSHIPS.length;
    const hasFilters = false;

    return (
        <Flex flex={1} direction={'column'} gap={'size-250'} UNSAFE_style={{ overflowY: 'hidden' }}>
            <Flex alignItems={'center'} gap={'size-200'}>
                <SearchField
                    placeholder={'Search by name'}
                    value={searchPhrase}
                    onChange={setSearchPhrase}
                    width={'size-4600'}
                />

                <OrganizationsStatusesPicker
                    selectedOrgStatus={selectedOrgStatus}
                    onChangeSelectedOrgStatus={setSelectedOrgStatus}
                />

                {totalCount > 0 && (
                    <EntitiesCounter
                        totalMatchedCount={totalMatchedCount}
                        totalCount={totalCount}
                        hasFilters={hasFilters}
                        entity={'membership'}
                    />
                )}
            </Flex>
            <View flex={1} overflow={'hidden'}>
                <MembershipsTable user={user} memberships={MOCKED_MEMBERSHIPS} />
            </View>
        </Flex>
    );
};

export const UserMemberships: FC = () => {
    return (
        <Flex direction={'column'} height={'100%'}>
            <Header title={'Memberships'} />
            <UserMembershipsMainContent />
        </Flex>
    );
};
