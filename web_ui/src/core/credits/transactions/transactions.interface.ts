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
