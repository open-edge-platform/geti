// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction, useState } from 'react';

import { USER_ROLE, UsersQueryParams } from '@geti/core/src/users/users.interface';
import { Flex, SearchField } from '@geti/ui';
import { isEmpty } from 'lodash-es';

import { useDebouncedCallback } from '../../../hooks/use-debounced-callback/use-debounced-callback.hook';
import { RolePicker } from './old-project-users/role-picker.component';
import { UsersCount } from './workspace-users/users-count.component';

interface WorkspaceUsersHeaderProps {
    totalCount: number;
    totalMatchedCount: number;
    hasFilterOptions: boolean;
    setUsersQueryParams: Dispatch<SetStateAction<UsersQueryParams>>;
    isProjectUsersTable?: boolean;
}

export const UsersHeader = ({
    totalMatchedCount,
    totalCount,
    hasFilterOptions,
    setUsersQueryParams,
    isProjectUsersTable = false,
}: WorkspaceUsersHeaderProps): JSX.Element => {
    const [searchInput, setSearchInput] = useState<string>('');
    const [roleFilter, setRoleFilter] = useState<USER_ROLE | undefined>();

    const roles = isProjectUsersTable
        ? [USER_ROLE.PROJECT_MANAGER, USER_ROLE.PROJECT_CONTRIBUTOR]
        : [USER_ROLE.WORKSPACE_ADMIN, USER_ROLE.WORKSPACE_CONTRIBUTOR];

    const debouncedCallback = useDebouncedCallback((value: string) => {
        setUsersQueryParams((prevQueryParams) => {
            const newQueryParams = { ...prevQueryParams };

            newQueryParams.name = value;

            if (value === '') {
                delete newQueryParams.name;
            }

            return newQueryParams;
        });
    }, 300);

    const handleSearchInputChange = (value: string) => {
        setSearchInput(value);

        debouncedCallback(value);
    };

    const changeRole = (role: USER_ROLE) => {
        setRoleFilter(role);
        setUsersQueryParams((prevQueryParams) => {
            if (isEmpty(role)) {
                const { role: roleParam, ...restParams } = prevQueryParams;

                return restParams;
            } else {
                return { ...prevQueryParams, role };
            }
        });
    };

    return (
        <Flex alignItems='center' justifyContent={'space-between'} marginY={'size-200'}>
            <Flex gap={'size-200'}>
                <SearchField
                    minWidth={'size-3000'}
                    value={searchInput}
                    onChange={handleSearchInputChange}
                    placeholder='Search by name or email'
                    aria-label='Search by name or email'
                    data-testid={'users-header-search-field'}
                />

                <RolePicker
                    roles={roles}
                    emptyItem={'All roles'}
                    selectedRole={roleFilter}
                    setSelectedRole={changeRole}
                    options={{ showLabel: false }}
                    testId={'users-header-role-picker'}
                />
            </Flex>
            <UsersCount
                totalMatchedCount={totalMatchedCount}
                totalCount={totalCount}
                hasFilters={hasFilterOptions}
                id={'users-header-users-count'}
            />
        </Flex>
    );
};
