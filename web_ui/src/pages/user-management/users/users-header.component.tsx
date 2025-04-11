// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Dispatch, SetStateAction, useState } from 'react';

import { Flex } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

import { USER_ROLE, UsersQueryParams } from '../../../core/users/users.interface';
import { useDebouncedCallback } from '../../../hooks/use-debounced-callback/use-debounced-callback.hook';
import { SearchField } from '../../../shared/components/search-field/search-field.component';
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
