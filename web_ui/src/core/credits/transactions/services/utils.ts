// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { TransactionsAggregatesDTO, TransactionsResponseDTO } from '../dtos/transactions.interface';
import { TransactionsAggregatesResponse, TransactionsResponse } from '../transactions.interface';

export const getTransactionResponseEntity = ({
    transactions,
    total,
    next_page,
    total_matched,
}: TransactionsResponseDTO): TransactionsResponse => {
    return {
        transactions: transactions.map((transaction) => ({
            credits: transaction.credits,
            workspaceId: transaction.workspace_id,
            projectId: transaction.project_id,
            serviceName: transaction.service_name,
            millisecondsTimestamp: transaction.milliseconds_timestamp,
        })),
        total,
        totalMatched: total_matched,
        nextPage: next_page ? { skip: next_page.skip, limit: next_page.limit } : null,
    };
};

export const getTransactionsAggregatesResponseEntity = ({
    aggregates,
    total,
    next_page,
    total_matched,
}: TransactionsAggregatesDTO): TransactionsAggregatesResponse => {
    return {
        aggregates,
        total,
        totalMatched: total_matched,
        nextPage: next_page ? { skip: next_page.skip, limit: next_page.limit } : null,
    };
};
