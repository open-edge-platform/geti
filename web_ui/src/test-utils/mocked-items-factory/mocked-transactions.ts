// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    CreditServiceName,
    Transaction,
    TransactionsAggregate,
    TransactionsAggregatesKey,
} from '../../core/credits/transactions/transactions.interface';

export const getMockedTransaction = (transaction: Partial<Transaction> = {}): Transaction => ({
    credits: 23,
    workspaceId: 'workspace_id_123',
    projectId: 'project_id_784',
    serviceName: CreditServiceName.OPTIMIZATION,
    millisecondsTimestamp: 1711312113376,
    ...transaction,
});

export const getMockedTransactionsAggregate = (
    aggregate: Partial<TransactionsAggregate> = {}
): TransactionsAggregate => ({
    group: [
        { key: TransactionsAggregatesKey.PROJECT, value: 'project_id_784' },
        { key: TransactionsAggregatesKey.SERVICE_NAME, value: 'optimization' },
    ],
    result: {
        credits: 23,
        resources: {
            images: 23,
        },
    },
    ...aggregate,
});
