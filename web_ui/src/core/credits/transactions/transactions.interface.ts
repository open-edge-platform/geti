// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { InfiniteQuery } from '../../shared/infinite-query.interface';

export enum CreditServiceName {
    TRAINING = 'training',
    OPTIMIZATION = 'optimization',
}

export enum TransactionsAggregatesKey {
    PROJECT = 'project',
    SERVICE_NAME = 'service_name',
    DATE = 'date',
}

export interface TransactionsAggregatesGroupItem {
    key: TransactionsAggregatesKey;
    value: number | string;
}

export interface Transaction {
    credits: number;
    workspaceId: string;
    projectId: string;
    projectName?: string;
    serviceName: CreditServiceName;
    millisecondsTimestamp: number;
}

export interface TransactionsResponse extends Omit<InfiniteQuery, 'totalCount'> {
    transactions: Transaction[];
    total: number;
    totalMatched: number;
}

export interface TransactionsAggregate {
    group: TransactionsAggregatesGroupItem[];
    projectName?: string;
    result: {
        credits: number;
        resources: {
            [key: string]: number | undefined;
        };
    };
}

export interface TransactionsAggregatesResponse extends Omit<InfiniteQuery, 'totalCount'> {
    aggregates: TransactionsAggregate[];
    total: number;
    totalMatched: number;
}
