// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { OrganizationIdentifier } from '../../../organizations/organizations.interface';
import {
    TransactionsAggregatesKey,
    TransactionsAggregatesResponse,
    TransactionsResponse,
} from '../transactions.interface';

export interface GetTransactionsAggregatesQueryOptions {
    keys: Set<TransactionsAggregatesKey>;
    fromDate?: string;
    toDate?: string;
    projectId?: string;
    skip?: number;
    limit?: number;
}

export interface GetTransactionsQueryOptions {
    fromDate?: string;
    toDate?: string;
    projectId?: string;
    skip?: number;
    limit?: number;
}

export interface TransactionsService {
    getTransactions: (
        id: OrganizationIdentifier,
        options: GetTransactionsQueryOptions
    ) => Promise<TransactionsResponse>;
    getTransactionsAggregates(
        id: OrganizationIdentifier,
        options: GetTransactionsAggregatesQueryOptions
    ): Promise<TransactionsAggregatesResponse>;
}
