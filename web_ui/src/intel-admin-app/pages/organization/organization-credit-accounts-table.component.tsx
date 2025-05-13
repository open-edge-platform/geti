// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    Cell,
    Column,
    Content,
    Heading,
    IllustratedMessage,
    Row,
    TableBody,
    TableHeader,
    TableView,
    Text,
    View,
} from '@adobe/react-spectrum';
import NotFound from '@spectrum-icons/illustrations/NotFound';
import dayjs from 'dayjs';
import { get } from 'lodash-es';

import { CreditAccount } from '../../../core/credits/credits.interface';
import { getBalanceUsedCredits } from '../../../core/credits/services/utils';
import { TableCellProps } from '../../../shared/components/table/table.interface';
import { SpectrumTableLoadingState } from '../../../shared/utils';
import { ActionsCell } from './cells/credit-accounts-actions-cell.component';
import { RenewalDayCell } from './cells/renewal-day-cell.component';

interface creditAccountsTableProps {
    creditAccounts: CreditAccount[];
    getNextPage: () => Promise<void>;
    isLoading: boolean;
    isLoadingNextPage: boolean;
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
    ACTIONS = 'actions',
}

const renderEmptyState = (): JSX.Element => (
    <IllustratedMessage>
        <NotFound />
        <Heading>No results</Heading>
        <Content>No credit accounts found</Content>
    </IllustratedMessage>
);

export const CreditAccountsTable: React.FC<React.PropsWithChildren<creditAccountsTableProps>> = ({
    creditAccounts,
    getNextPage,
    isLoading,
    isLoadingNextPage,
}) => {
    const columns = [
        {
            label: 'Credit Account Name',
            dataKey: CREDIT_ACCOUNTS_TABLE_COLUMNS.NAME,
            component: ({ cellData }: CreditAccountsTableCellProps) => <Text>{cellData}</Text>,
        },
        {
            label: 'Available Credits',
            dataKey: CREDIT_ACCOUNTS_TABLE_COLUMNS.AMOUNT_AVAILABLE,
            component: ({ rowData }: CreditAccountsTableCellProps) => <Text>{rowData.balance.available}</Text>,
        },
        {
            label: 'Used Credits',
            dataKey: CREDIT_ACCOUNTS_TABLE_COLUMNS.AMOUNT_USED,
            component: ({ rowData: { balance } }: CreditAccountsTableCellProps) => (
                <Text>{getBalanceUsedCredits(balance)}</Text>
            ),
        },
        {
            label: 'Pending Credits',
            dataKey: CREDIT_ACCOUNTS_TABLE_COLUMNS.AMOUNT_PENDING,
            component: ({ rowData }: CreditAccountsTableCellProps) => <Text>{rowData.balance.blocked}</Text>,
        },
        {
            label: 'Recurrence',
            dataKey: CREDIT_ACCOUNTS_TABLE_COLUMNS.RENEWAL,
            component: ({ rowData }: CreditAccountsTableCellProps) => <RenewalDayCell rowData={rowData} />,
        },
        {
            label: 'Expiration Date',
            dataKey: CREDIT_ACCOUNTS_TABLE_COLUMNS.EXPIRES,
            component: ({ cellData }: CreditAccountsTableCellProps) => {
                return <Text>{cellData !== null ? dayjs(cellData).format('D MMM YYYY') : 'Never'}</Text>;
            },
        },
        {
            label: 'Actions',
            dataKey: CREDIT_ACCOUNTS_TABLE_COLUMNS.ACTIONS,
            component: ({ rowData }: CreditAccountsTableCellProps) => <ActionsCell rowData={rowData} />,
        },
    ];

    return (
        <View height={'100%'} width={'100%'}>
            <TableView
                id='organization-credit-accounts-table-id'
                aria-label='Organization Credit Accounts Table'
                selectionMode='none'
                height={creditAccounts.length ? '100%' : 'size-3000'}
                density='spacious'
                renderEmptyState={renderEmptyState}
            >
                <TableHeader columns={columns}>
                    {({ label, dataKey: key }) => (
                        <Column key={key} hideHeader={key === CREDIT_ACCOUNTS_TABLE_COLUMNS.ACTIONS}>
                            {label}
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

                                const cellProps: CreditAccountsTableCellProps = {
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
