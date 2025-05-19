// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction } from 'react';

import { Cell, Column, Flex, Row, TableBody, TableHeader, TableView, View } from '@geti/ui';
import { useQueryClient } from '@tanstack/react-query';
import { get } from 'lodash-es';

import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { Organization } from '../../../core/organizations/organizations.interface';
import { GetOrganizationsQueryOptions } from '../../../core/organizations/services/organizations-service.interface';
import QUERY_KEYS from '../../../core/requests/query-keys';
import { paths } from '../../../core/services/routes';
import { useSortTable } from '../../../hooks/use-sort-table/use-sort-table.hook';
import { DateCell } from '../../../shared/components/table/date-cell/date-cell.component';
import { StatusCell } from '../../../shared/components/table/status-cell/status-cell.component';
import { TableCellProps } from '../../../shared/components/table/table.interface';
import { SpectrumTableLoadingState } from '../../../shared/utils';
import { OrganizationAdminsCell } from './cells/organization-admins-cell.component';
import { OrganizationNameCell } from './cells/organization-name-cell.component';
import { OrganizationsMenu } from './organizations-menu.component';

interface OrganizationsTableProps {
    organizations: Organization[];
    getNextPage: () => Promise<void>;
    isLoading: boolean;
    isFetchingNextPage: boolean;
    queryOptions: GetOrganizationsQueryOptions;
    setOrganizationsQueryOptions: Dispatch<SetStateAction<GetOrganizationsQueryOptions>>;
}

enum ORGANIZATIONS_COLUMNS_KEYS {
    ORGANIZATION_NAME = 'name',
    ADMINS = 'createdBy',
    STATUS = 'status',
    CREATION_DATE = 'createdAt',
    ACTIONS = 'actions',
}

export const OrganizationsTable = ({
    organizations,
    getNextPage,
    queryOptions,
    isLoading,
    isFetchingNextPage,
    setOrganizationsQueryOptions,
}: OrganizationsTableProps): JSX.Element => {
    const queryClient = useQueryClient();
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();

    const columns = [
        {
            label: 'Organization',
            dataKey: ORGANIZATIONS_COLUMNS_KEYS.ORGANIZATION_NAME,
            component: (props: TableCellProps) => (
                <OrganizationNameCell id={props.rowData.id} name={props.rowData.name} />
            ),
            isSortable: true,
        },
        {
            label: 'Admins',
            dataKey: ORGANIZATIONS_COLUMNS_KEYS.ADMINS,
            component: (props: TableCellProps) => <OrganizationAdminsCell {...props} />,
            isSortable: false,
        },
        {
            label: 'Status',
            dataKey: ORGANIZATIONS_COLUMNS_KEYS.STATUS,
            component: ({ rowData, dataKey }: TableCellProps) => (
                <StatusCell key={rowData.id} id={`${rowData.id}-${dataKey}`} status={rowData.status} />
            ),
            isSortable: true,
        },
        {
            label: 'Membership since',
            dataKey: ORGANIZATIONS_COLUMNS_KEYS.CREATION_DATE,
            isSortable: true,
            component: ({ rowData, dataKey }: TableCellProps) => (
                <DateCell key={rowData.id} id={`${rowData.id}-${dataKey}`} date={rowData.createdAt} direction={'row'} />
            ),
        },
        {
            label: '',
            dataKey: ORGANIZATIONS_COLUMNS_KEYS.ACTIONS,
            component: ({ rowData }: TableCellProps) => <OrganizationsMenu key={rowData.id} organization={rowData} />,
        },
    ];

    const setQueryOptionsHandler: Dispatch<SetStateAction<GetOrganizationsQueryOptions>> = async (options) => {
        await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.ORGANIZATIONS({}) });
        setOrganizationsQueryOptions(options);
    };

    const [sortingOptions, sort] = useSortTable<GetOrganizationsQueryOptions>({
        queryOptions,
        setQueryOptions: setQueryOptionsHandler,
    });

    return (
        <Flex flex={1} width={'100%'} height={'100%'}>
            <View height={'100%'} minHeight={0} width={'100%'}>
                <TableView
                    id='organizations-table-id'
                    aria-label='Organizations table'
                    selectionMode='none'
                    minHeight={'size-2000'}
                    maxHeight={'100%'}
                    onSortChange={(change) => {
                        sort({
                            sortBy: String(change.column),
                            sortDirection: change.direction === 'ascending' ? 'ASC' : 'DESC',
                        });
                    }}
                    sortDescriptor={{
                        column: sortingOptions.sortBy ?? ORGANIZATIONS_COLUMNS_KEYS.ORGANIZATION_NAME,
                        direction: sortingOptions.sortDirection === 'ASC' ? 'ascending' : 'descending',
                    }}
                >
                    <TableHeader columns={columns}>
                        {({ label, dataKey: key, isSortable: allowsSorting }) => (
                            <Column
                                key={key}
                                allowsSorting={allowsSorting}
                                hideHeader={key === ORGANIZATIONS_COLUMNS_KEYS.ACTIONS}
                            >
                                {label.toLocaleUpperCase()}
                            </Column>
                        )}
                    </TableHeader>
                    <TableBody
                        items={organizations}
                        loadingState={
                            isLoading
                                ? SpectrumTableLoadingState.loading
                                : isFetchingNextPage
                                  ? SpectrumTableLoadingState.loadingMore
                                  : SpectrumTableLoadingState.idle
                        }
                        onLoadMore={getNextPage}
                    >
                        {(organization) => {
                            return (
                                <Row
                                    key={organization.id}
                                    href={
                                        FEATURE_FLAG_CREDIT_SYSTEM
                                            ? paths.intelAdmin.organization.overview({
                                                  organizationId: organization.id,
                                              })
                                            : undefined
                                    }
                                    routerOptions={{ viewTransition: true }}
                                >
                                    {(columnKey) => {
                                        const column = columns.find(({ dataKey }) => dataKey === columnKey);

                                        if (column === undefined) {
                                            return <Cell>N/A</Cell>;
                                        }

                                        const cellProps: TableCellProps = {
                                            cellData: get(organization, `${columnKey}`, 'N/A'),
                                            rowData: organization,
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
        </Flex>
    );
};
