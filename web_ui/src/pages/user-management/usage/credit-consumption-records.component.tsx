// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import {
    ActionButton,
    Cell,
    Column,
    DateRangePicker,
    dimensionValue,
    Flex,
    Form,
    Heading,
    Row,
    TableBody,
    TableHeader,
    TableView,
    Text,
    View,
} from '@geti/ui';
import { Refresh } from '@geti/ui/icons';
import { getLocalTimeZone } from '@internationalized/date';
import { isNil } from 'lodash-es';
import { DateValue } from 'react-aria';

import { useTransactionsQueries } from '../../../core/credits/transactions/hooks/use-transactions.hook';
import { useFirstWorkspaceIdentifier } from '../../../providers/workspaces-provider/use-first-workspace-identifier.hook';
import { getClassServiceName } from '../../../shared/components/header/credit-balance/util';
import { NotFound } from '../../../shared/components/not-found/not-found.component';
import { formatDate, SpectrumTableLoadingState } from '../../../shared/utils';

import classes from './usage.module.scss';

const getMilliseconds = (date: DateValue) => String(date.toDate(getLocalTimeZone()).getTime());

export const CreditConsumptionRecords = (): JSX.Element => {
    const { organizationId, workspaceId } = useFirstWorkspaceIdentifier();
    const { useGetTransactions } = useTransactionsQueries();
    const [filterByDate, setFilterByDate] = useState<undefined | { fromDate: string; toDate: string }>(undefined);

    const { transactions, isPending, isFetchingNextPage, getNextPage } = useGetTransactions(
        { organizationId, workspaceId },
        {
            fromDate: filterByDate?.fromDate,
            toDate: filterByDate?.toDate,
            limit: 10,
        }
    );

    return (
        <View marginTop={'size-600'}>
            <Heading level={5} marginBottom={0} UNSAFE_style={{ fontSize: dimensionValue('size-250') }}>
                Credit consumption by records
            </Heading>

            <Flex gap={'size-200'} alignItems={'center'} marginTop={'size-300'}>
                <Form validationBehavior='native'>
                    <Flex gap={'size-50'} alignItems={'center'} marginTop={0}>
                        <DateRangePicker
                            onChange={(rangeValue) => {
                                const filterDate = !isNil(rangeValue)
                                    ? {
                                          fromDate: getMilliseconds(rangeValue.start),
                                          toDate: getMilliseconds(rangeValue.end.add({ days: 1 })),
                                      }
                                    : undefined;

                                setFilterByDate(filterDate);
                            }}
                        />
                        <ActionButton isQuiet type={'reset'} aria-label={'reset calendar'}>
                            <Refresh />
                        </ActionButton>
                    </Flex>
                </Form>
            </Flex>

            <TableView
                isQuiet
                height={'size-3600'}
                density={'spacious'}
                marginTop={'size-300'}
                UNSAFE_className={classes.consumptionByRecordsTable}
                aria-label={'table consumption by records'}
                renderEmptyState={() => <NotFound />}
            >
                <TableHeader>
                    <Column>Usage type</Column>
                    <Column>Project</Column>
                    <Column>Credits used</Column>
                    <Column>Timestamp</Column>
                </TableHeader>
                <TableBody
                    items={transactions}
                    loadingState={
                        isPending
                            ? SpectrumTableLoadingState.loading
                            : isFetchingNextPage
                              ? SpectrumTableLoadingState.loadingMore
                              : SpectrumTableLoadingState.idle
                    }
                    onLoadMore={getNextPage}
                >
                    {(transaction) => (
                        <Row
                            key={`${transaction.projectName}-
                                    ${transaction.serviceName}-
                                    ${transaction.millisecondsTimestamp}`}
                        >
                            <Cell>
                                <Text UNSAFE_className={getClassServiceName(transaction.serviceName)}>
                                    {transaction.serviceName}
                                </Text>
                            </Cell>
                            <Cell>{transaction.projectName}</Cell>
                            <Cell>{transaction.credits}</Cell>
                            <Cell>
                                <Text UNSAFE_style={{ display: 'block' }}>
                                    {formatDate(transaction.millisecondsTimestamp, 'DD MMM YY')}
                                </Text>
                                <Text UNSAFE_style={{ display: 'block', fontSize: dimensionValue('size-130') }}>
                                    {formatDate(transaction.millisecondsTimestamp, 'HH:mm:ss')}
                                </Text>
                            </Cell>
                        </Row>
                    )}
                </TableBody>
            </TableView>
        </View>
    );
};
