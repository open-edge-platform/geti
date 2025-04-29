// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction, useMemo } from 'react';

import { Cell, Column, Flex, Row, TableBody, TableHeader, TableView, View } from '@adobe/react-spectrum';
import get from 'lodash/get';
import isEmpty from 'lodash/isEmpty';

import { isOrganizationAdmin } from '../../../../core/users/user-role-utils';
import { User, UsersQueryParams } from '../../../../core/users/users.interface';
import { Workspace } from '../../../../core/workspaces/services/workspaces.interface';
import { useSortTable } from '../../../../hooks/use-sort-table/use-sort-table.hook';
import { NotFound } from '../../../../shared/components/not-found/not-found.component';
import { CasualCell } from '../../../../shared/components/table/components/casual-cell/casual-cell.component';
import { StatusCell } from '../../../../shared/components/table/status-cell/status-cell.component';
import { TableCellProps } from '../../../../shared/components/table/table.interface';
import { SpectrumTableLoadingState } from '../../../../shared/utils';
import { LastLoginCell } from './last-login-cell.component';
import { ProjectRoleCell } from './project-role-cell.component';
import { UserNameCell } from './user-name-cell/user-name-cell.component';
import { getUserFullName } from './utils';
import { WorkspacesRoleCell } from './workspaces-role-cell.component';

export const enum USERS_TABLE_COLUMNS {
    EMAIL_ADDRESS = 'email',
    LAST_NAME = 'lastName',
    ROLES = 'roles',
    REGISTRATION_STATUS = 'status',
    LAST_LOGIN = 'lastSuccessfulLogin',
    MORE_ACTIONS = 'moreActions',
}

interface UsersTableProps {
    totalCount: number;
    users: User[];
    activeUser: User;
    hasFilters: boolean;
    isLoading: boolean;
    isFetchingNextPage: boolean;
    getNextPage: () => Promise<void>;
    usersQueryParams: UsersQueryParams;
    setUsersQueryParams: Dispatch<SetStateAction<UsersQueryParams>>;
    UserActions: (props: { activeUser: User; user: User; users: User[] }) => JSX.Element;
    ignoredColumns?: USERS_TABLE_COLUMNS[];
    resourceId: string | undefined;
    workspaces: Workspace[];
    isProjectUsersTable?: boolean;
    organizationId: string;
}

export const UsersTable = ({
    users,
    hasFilters,
    activeUser,
    usersQueryParams,
    setUsersQueryParams,
    UserActions,
    ignoredColumns = [],
    resourceId,
    isLoading,
    isFetchingNextPage,
    organizationId,
    isProjectUsersTable,
    workspaces,
    getNextPage,
}: UsersTableProps): JSX.Element => {
    const shouldShowNotFound = hasFilters && isEmpty(users);

    const columns = useMemo(() => {
        const tableColumns = [
            {
                label: 'Name',
                dataKey: USERS_TABLE_COLUMNS.LAST_NAME,
                width: 210,
                isSortable: true,
                component: ({ rowData, dataKey }: TableCellProps) => {
                    const { id, firstName, lastName, email, userPhoto } = rowData;

                    const fullName = getUserFullName(firstName, lastName);
                    const cellData = isEmpty(fullName) ? '-' : activeUser?.id === id ? `${fullName} (You)` : fullName;
                    const isOrgAdmin = isOrganizationAdmin(rowData, organizationId);

                    return (
                        <UserNameCell
                            key={id}
                            id={id}
                            cellData={cellData}
                            email={email}
                            dataKey={dataKey}
                            userPhoto={userPhoto}
                            fullName={`${firstName} ${lastName}`}
                            isOrgAdmin={isOrgAdmin}
                        />
                    );
                },
            },
            {
                label: 'Email address',
                dataKey: USERS_TABLE_COLUMNS.EMAIL_ADDRESS,
                width: 240,
                isSortable: true,
                component: (data: TableCellProps): JSX.Element => {
                    return <CasualCell {...data} />;
                },
            },
            {
                label: isEmpty(resourceId) ? 'Workspace' : 'Role',
                dataKey: USERS_TABLE_COLUMNS.ROLES,
                width: 150,
                isSortable: false,
                component: (data: TableCellProps) => {
                    return isProjectUsersTable ? (
                        <ProjectRoleCell {...data} roles={data.rowData.roles} projectId={resourceId as string} />
                    ) : (
                        <WorkspacesRoleCell
                            {...data}
                            workspaceId={resourceId}
                            workspaces={workspaces}
                            cellData={data.rowData.roles}
                        />
                    );
                },
            },
            {
                label: 'Last login',
                dataKey: USERS_TABLE_COLUMNS.LAST_LOGIN,
                width: 150,
                isSortable: true,
                component: ({ rowData, dataKey }: TableCellProps) => (
                    <LastLoginCell
                        key={rowData.id}
                        id={`${rowData.id}-${dataKey}`}
                        lastSuccessfulLogin={rowData.lastSuccessfulLogin}
                    />
                ),
            },
            {
                label: 'Registration',
                dataKey: USERS_TABLE_COLUMNS.REGISTRATION_STATUS,
                width: 180,
                isSortable: true,
                component: ({ rowData, dataKey }: TableCellProps) => {
                    return <StatusCell key={rowData.id} id={`${rowData.id}-${dataKey}`} status={rowData.status} />;
                },
            },
            {
                label: '',
                dataKey: USERS_TABLE_COLUMNS.MORE_ACTIONS,
                width: 50,
                isSortable: false,
                component: ({ rowData }: TableCellProps): JSX.Element => {
                    return <UserActions activeUser={activeUser} user={rowData} users={users} />;
                },
            },
        ];

        return tableColumns.filter(({ dataKey }) => !ignoredColumns.includes(dataKey as USERS_TABLE_COLUMNS));
    }, [ignoredColumns, resourceId, UserActions, activeUser, isProjectUsersTable, organizationId, workspaces, users]);

    const [sortingOptions, sort] = useSortTable<UsersQueryParams>({
        queryOptions: usersQueryParams,
        setQueryOptions: setUsersQueryParams,
    });

    return (
        <Flex flex={1} width={'100%'} justifyContent={'center'} alignItems={'center'}>
            {shouldShowNotFound ? (
                <NotFound />
            ) : (
                <View height={'100%'} minHeight={0} width={'100%'} data-testid={'users-table-id'}>
                    <TableView
                        id='users-table-id'
                        aria-label='Users table'
                        selectionMode='none'
                        onSortChange={(change) => {
                            sort({
                                sortBy: String(change.column),
                                sortDirection: change.direction === 'ascending' ? 'ASC' : 'DESC',
                            });
                        }}
                        sortDescriptor={
                            sortingOptions.sortDirection !== undefined && sortingOptions.sortBy !== undefined
                                ? {
                                      column: sortingOptions.sortBy,
                                      direction: sortingOptions.sortDirection === 'ASC' ? 'ascending' : 'descending',
                                  }
                                : undefined
                        }
                    >
                        <TableHeader columns={columns}>
                            {({ label, dataKey: key, isSortable: allowsSorting, width }) => (
                                <Column
                                    key={key}
                                    allowsSorting={allowsSorting}
                                    align={key === USERS_TABLE_COLUMNS.MORE_ACTIONS ? 'end' : 'start'}
                                    maxWidth={key === USERS_TABLE_COLUMNS.MORE_ACTIONS ? width : undefined}
                                    minWidth={
                                        key === USERS_TABLE_COLUMNS.EMAIL_ADDRESS ||
                                        key === USERS_TABLE_COLUMNS.LAST_NAME
                                            ? width
                                            : undefined
                                    }
                                >
                                    {label}
                                </Column>
                            )}
                        </TableHeader>
                        <TableBody
                            items={users}
                            onLoadMore={getNextPage}
                            loadingState={
                                isLoading
                                    ? SpectrumTableLoadingState.loading
                                    : isFetchingNextPage
                                      ? SpectrumTableLoadingState.loadingMore
                                      : undefined
                            }
                        >
                            {(user) => {
                                return (
                                    <Row key={user.id}>
                                        {(columnKey) => {
                                            const column = columns.find(({ dataKey }) => dataKey === columnKey);

                                            if (column === undefined) {
                                                return <Cell>N/A</Cell>;
                                            }

                                            const cellProps: TableCellProps = {
                                                cellData: get(user, `${columnKey}`, 'N/A'),
                                                rowData: user,
                                                dataKey: `${columnKey}`,
                                                isScrolling: false,
                                                columnIndex: 1,
                                                rowIndex: 1,
                                            };

                                            return <Cell>{<column.component {...cellProps} />}</Cell>;
                                        }}
                                    </Row>
                                );
                            }}
                        </TableBody>
                    </TableView>
                </View>
            )}
        </Flex>
    );
};
