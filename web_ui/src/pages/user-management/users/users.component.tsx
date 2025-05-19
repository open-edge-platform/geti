// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, useState } from 'react';

import { Flex } from '@geti/ui';
import { motion } from 'framer-motion';
import { isEmpty } from 'lodash-es';

import { useUsers } from '../../../core/users/hook/use-users.hook';
import { RESOURCE_TYPE, User, UsersQueryParams } from '../../../core/users/users.interface';
import { useOrganizationIdentifier } from '../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { useWorkspaces } from '../../../providers/workspaces-provider/workspaces-provider.component';
import { ANIMATION_PARAMETERS } from '../../../shared/animation-parameters/animation-parameters';
import { UsersHeader } from './users-header.component';
import { UsersTable } from './users-table/users-table.component';

interface UsersProps {
    activeUser: User;
    resourceType: RESOURCE_TYPE;
    resourceId: string | undefined;
    UserActions?: ComponentProps<typeof UsersTable>['UserActions'];
    ignoredColumns?: ComponentProps<typeof UsersTable>['ignoredColumns'];
    isProjectUsersTable?: ComponentProps<typeof UsersTable>['isProjectUsersTable'];
}

const USERS_LIMIT = 20;

export const Users = ({
    resourceType,
    resourceId,
    activeUser,
    UserActions = () => <></>,
    ignoredColumns = [],
    isProjectUsersTable = false,
}: UsersProps): JSX.Element => {
    const { organizationId } = useOrganizationIdentifier();
    const { workspaces } = useWorkspaces();
    const [usersQueryParams, setUsersQueryParams] = useState<UsersQueryParams>({
        sortBy: undefined,
        sortDirection: undefined,
    });
    const { useGetUsersQuery } = useUsers();
    const { users, totalCount, totalMatchedCount, isLoading, getNextPage, isFetchingNextPage } = useGetUsersQuery(
        organizationId,
        {
            ...usersQueryParams,
            limit: USERS_LIMIT,
            resourceId,
            resourceType,
        }
    );

    // sortBy and sortDirection are not filters

    const { sortBy, sortDirection, ...filteringParams } = usersQueryParams;
    const hasFilters = !isEmpty(filteringParams);

    return (
        <motion.div
            variants={ANIMATION_PARAMETERS.FADE_ITEM}
            initial={'hidden'}
            animate={'visible'}
            style={{ height: '100%' }}
        >
            <Flex direction={'column'} height={'100%'}>
                <UsersHeader
                    totalMatchedCount={totalMatchedCount}
                    totalCount={totalCount}
                    hasFilterOptions={hasFilters}
                    setUsersQueryParams={setUsersQueryParams}
                    isProjectUsersTable={isProjectUsersTable}
                />
                <UsersTable
                    isFetchingNextPage={isFetchingNextPage}
                    isLoading={isLoading}
                    totalCount={totalCount}
                    users={users}
                    hasFilters={hasFilters}
                    activeUser={activeUser}
                    getNextPage={getNextPage}
                    usersQueryParams={usersQueryParams}
                    setUsersQueryParams={setUsersQueryParams}
                    UserActions={UserActions}
                    ignoredColumns={ignoredColumns}
                    resourceId={resourceId}
                    workspaces={workspaces}
                    isProjectUsersTable={isProjectUsersTable}
                    organizationId={organizationId}
                />
            </Flex>
        </motion.div>
    );
};
