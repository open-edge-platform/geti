// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
