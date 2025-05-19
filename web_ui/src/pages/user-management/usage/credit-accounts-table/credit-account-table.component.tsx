// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, PropsWithChildren } from 'react';

import {
    Cell,
    Column,
    Content,
    Heading,
    Row,
    TableBody,
    TableHeader,
    TableView,
    Text,
    View,
    type AriaLabelingProps,
    type ColumnSize,
    type DOMProps,
    type StyleProps,
} from '@geti/ui';
import dayjs from 'dayjs';
import { get } from 'lodash-es';

import { CreditAccount } from '../../../../core/credits/credits.interface';
import { getBalanceUsedCredits } from '../../../../core/credits/services/utils';
import { TableCellProps } from '../../../../shared/components/table/table.interface';
import { TruncatedTextWithTooltip } from '../../../../shared/components/truncated-text/truncated-text.component';
import { SpectrumTableLoadingState } from '../../../../shared/utils';
import { RenewalDayCell } from './renewal-day-cell.component';

interface creditAccountsTableProps extends DOMProps, AriaLabelingProps, StyleProps {
    creditAccounts: CreditAccount[];
    isLoading: boolean;
    isLoadingNextPage?: boolean;
    getNextPage?: () => Promise<void>;
}

interface CreditAccountsTableCellProps extends TableCellProps {
    rowData: CreditAccount;
}

enum CREDIT_ACCOUNTS_TABLE_COLUMNS {
    NAME = 'name',
    AMOUNT_AVAILABLE = 'amountAvailable',
    AMOUNT_USED = 'amountUsed',
    AMOUNT_PENDING = 'amountPending',
    RENEWAL = 'renewalDayOfMonth',
    EXPIRES = 'expires',
}

const renderEmptyState = (): JSX.Element => (
    <>
        <Heading UNSAFE_style={{ textAlign: 'center' }}>No results</Heading>
        <Content>No credit accounts found</Content>
    </>
);

export const CreditAccountsTable: FC<PropsWithChildren<creditAccountsTableProps>> = ({
    creditAccounts,
    getNextPage,
    isLoading,
    isLoadingNextPage,
    ...rest
}) => {
    const columns = [
        {
            label: 'Credit Account',
            dataKey: CREDIT_ACCOUNTS_TABLE_COLUMNS.NAME,
            component: ({ cellData }: TableCellProps) => (
                <TruncatedTextWithTooltip>{cellData}</TruncatedTextWithTooltip>
            ),
            width: '3fr',
        },
        {
            label: 'Available',
            dataKey: CREDIT_ACCOUNTS_TABLE_COLUMNS.AMOUNT_AVAILABLE,
            component: ({ rowData }: CreditAccountsTableCellProps) => <Text>{rowData.balance.available}</Text>,
            width: '1.7fr',
        },
        {
            label: 'Used',
            dataKey: CREDIT_ACCOUNTS_TABLE_COLUMNS.AMOUNT_USED,
            component: ({ rowData: { balance } }: CreditAccountsTableCellProps) => (
                <Text>{getBalanceUsedCredits(balance)}</Text>
            ),
            width: '1.7fr',
        },
        {
            label: 'Pending',
            dataKey: CREDIT_ACCOUNTS_TABLE_COLUMNS.AMOUNT_PENDING,
            component: ({ rowData: { balance } }: CreditAccountsTableCellProps) => <Text>{balance.blocked}</Text>,
            width: '1.7fr',
        },
        {
            label: 'Recurrence',
            dataKey: CREDIT_ACCOUNTS_TABLE_COLUMNS.RENEWAL,
            component: ({ rowData }: CreditAccountsTableCellProps) => <RenewalDayCell rowData={rowData} />,
            width: '2.6fr',
        },
        {
            label: 'Expires',
            dataKey: CREDIT_ACCOUNTS_TABLE_COLUMNS.EXPIRES,
            component: ({ cellData }: CreditAccountsTableCellProps) => {
                return (
                    <TruncatedTextWithTooltip>
                        {cellData !== null ? dayjs(cellData).format('D MMM YYYY') : 'Never'}
                    </TruncatedTextWithTooltip>
                );
            },
            width: '2fr',
        },
    ];

    return (
        <View width='100%'>
            <TableView
                aria-label='Credit Accounts Table'
                selectionMode='none'
                density='spacious'
                height={creditAccounts.length ? '100%' : 'size-1600'}
                renderEmptyState={renderEmptyState}
                {...rest}
            >
                <TableHeader columns={columns}>
                    {({ label, dataKey: key, width }) => (
                        <Column key={key} width={width as ColumnSize}>
                            <TruncatedTextWithTooltip>{label}</TruncatedTextWithTooltip>
                        </Column>
                    )}
                </TableHeader>
                <TableBody
                    items={creditAccounts}
                    loadingState={
                        isLoading
                            ? SpectrumTableLoadingState.loading
                            : isLoadingNextPage
                              ? SpectrumTableLoadingState.loadingMore
                              : SpectrumTableLoadingState.idle
                    }
                    onLoadMore={getNextPage}
                >
                    {(creditAccount) => (
                        <Row key={creditAccount.id}>
                            {(columnKey) => {
                                const column = columns.find(({ dataKey }) => dataKey === columnKey);

                                if (column === undefined) {
                                    return <Cell>N/A</Cell>;
                                }

                                const cellProps: TableCellProps = {
                                    cellData: get(creditAccount, `${columnKey}`, 'N/A'),
                                    rowData: creditAccount,
                                    dataKey: `${columnKey}`,
                                    isScrolling: false,
                                    columnIndex: 1,
                                    rowIndex: 1,
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
