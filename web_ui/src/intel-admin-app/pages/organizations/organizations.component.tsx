// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { Flex, View } from '@adobe/react-spectrum';

import {
    ORGANIZATIONS_QUERY_LIMIT,
    useOrganizationsApi,
} from '../../../core/organizations/hook/use-organizations-api.hook';
import { GetOrganizationsQueryOptions } from '../../../core/organizations/services/organizations-service.interface';
import { InvitationHeader } from './invitation-header.component';
import { OrganizationsFilters } from './organizations-filters.component';
import { OrganizationsTable } from './organizations-table.component';

// We want to show proper count messages (x out of y) only when name or status filter is applied
const hasFilters = (filters: GetOrganizationsQueryOptions): boolean => {
    return filters.name !== undefined || filters.status !== undefined;
};

export const Organizations = (): JSX.Element => {
    const [organizationsQueryOptions, setOrganizationsQueryOptions] = useState<GetOrganizationsQueryOptions>({
        sortBy: 'createdAt',
        sortDirection: 'DESC',
        limit: ORGANIZATIONS_QUERY_LIMIT,
    });

    const { useOrganizationsQuery } = useOrganizationsApi();

    const { organizations, totalCount, totalMatchedCount, getNextPage, isLoading, isFetchingNextPage } =
        useOrganizationsQuery(organizationsQueryOptions);

    return (
        <Flex direction={'column'} height={'100%'} gap={'size-50'}>
            <Flex justifyContent={'space-between'} alignItems={'center'}>
                <OrganizationsFilters
                    totalCount={totalCount}
                    hasFilters={hasFilters(organizationsQueryOptions)}
                    totalMatchedCount={totalMatchedCount}
                    setOrganizationsQueryOptions={setOrganizationsQueryOptions}
                />
                <InvitationHeader organizationsQueryOptions={organizationsQueryOptions} />
            </Flex>
            <View flex={1} overflow={'auto scroll'}>
                <OrganizationsTable
                    organizations={organizations}
                    isFetchingNextPage={isFetchingNextPage}
                    isLoading={isLoading}
                    getNextPage={getNextPage}
                    queryOptions={organizationsQueryOptions}
                    setOrganizationsQueryOptions={setOrganizationsQueryOptions}
                />
            </View>
        </Flex>
    );
};
