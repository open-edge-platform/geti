// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Cell, Column, Row, TableBody, TableHeader, TableView, Text, View } from '@geti/ui';
import { get } from 'lodash-es';

import { useSubscriptions } from '../../../core/credits/subscriptions/hooks/use-subscription-api.hook';
import { Quota } from '../../../core/credits/subscriptions/quotas.interface';
import { TableCellProps } from '../../../shared/components/table/table.interface';
import { isNonEmptyArray, SpectrumTableLoadingState } from '../../../shared/utils';
import { ActionCell } from './cells/service-limits-actions-cell.component';
import { useOrganization } from './hooks/organization.hook';

import classes from './organization.module.scss';

const SERVICE_LIMITS_QUERY_LIMIT = 10;

interface ServiceLimitTableCellProps {
    rowData: Quota;
    cellData: TableCellProps['cellData'];
    dataKey: TableCellProps['dataKey'];
}

enum SERVICE_LIMITS_TABLE_COLUMNS {
    SERVICE_LIMIT_NAME = 'quota_name',
    LIMIT = 'limit',
    UPDATED = 'updated',
    ACTIONS = 'actions',
}

const columns = [
    {
        label: 'Service limit name',
        dataKey: SERVICE_LIMITS_TABLE_COLUMNS.SERVICE_LIMIT_NAME,
        component: ({ rowData }: ServiceLimitTableCellProps) => (
            <View>
                <Text>{rowData.quotaName}</Text>
                <br />
                <Text UNSAFE_className={classes.tableCellSecondaryText}>{rowData.serviceName}</Text>
            </View>
        ),
    },
    {
        label: 'Limit',
        dataKey: SERVICE_LIMITS_TABLE_COLUMNS.LIMIT,
        component: ({ rowData }: ServiceLimitTableCellProps) => <Text>{rowData.limit}</Text>,
    },
    {
        label: 'Updated',
        dataKey: SERVICE_LIMITS_TABLE_COLUMNS.UPDATED,
        component: ({ rowData }: ServiceLimitTableCellProps) => (
            <Text>{rowData.updated ? new Date(rowData.updated).toLocaleDateString() : 'N/A'}</Text>
        ),
    },
    {
        label: 'Actions',
        dataKey: SERVICE_LIMITS_TABLE_COLUMNS.ACTIONS,
        hideHeader: true,
        component: ({ rowData }: ServiceLimitTableCellProps) => <ActionCell rowData={rowData} />,
    },
];

export const OrganizationServiceLimitsTable = () => {
    const { organizationId } = useOrganization();
    const { useGetOrganizationQuotasQuery } = useSubscriptions();
    const { quotas, isLoading, isFetchingNextPage, getNextPage } = useGetOrganizationQuotasQuery(
        { organizationId },
        { limit: SERVICE_LIMITS_QUERY_LIMIT }
    );

    return (
        <View height='100%' width='100%'>
            <TableView
                id='organization-service-limits-table'
                aria-label='Organization service limits table'
                selectionMode='none'
                minHeight={isNonEmptyArray(quotas) ? 'auto' : 'size-2000'}
                density='spacious'
                renderEmptyState={() => <>Organization hasn&apos;t subscribed yet to any Intel Geti products.</>}
            >
                <TableHeader columns={columns}>
                    {({ label, dataKey, hideHeader }) => (
                        <Column key={dataKey} hideHeader={hideHeader}>
                            {label}
                        </Column>
                    )}
                </TableHeader>
                <TableBody
                    items={quotas}
                    loadingState={
                        isLoading
                            ? SpectrumTableLoadingState.loading
                            : isFetchingNextPage
                              ? SpectrumTableLoadingState.loadingMore
                              : SpectrumTableLoadingState.idle
                    }
                    onLoadMore={getNextPage}
                >
                    {(quota) => (
                        <Row key={quota.id}>
                            {(columnKey) => {
                                const column = columns.find(({ dataKey }) => dataKey === columnKey);

                                if (column === undefined) {
                                    return <Cell>N/A</Cell>;
                                }

                                const cellProps: ServiceLimitTableCellProps = {
                                    cellData: get(quota, `${columnKey}`, 'N/A'),
                                    rowData: quota,
                                    dataKey: `${columnKey}`,
                                };

                                return <Cell>{<column.component {...cellProps} />}</Cell>;
                            }}
                        </Row>
                    )}
                </TableBody>
            </TableView>
        </View>
    );
};
