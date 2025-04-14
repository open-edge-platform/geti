// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CreditServiceName, TransactionsAggregatesKey } from '../transactions.interface';
import { TransactionsService } from './transactions-service.interface';

export const createInMemoryTransactionsService = (): TransactionsService => {
    const getTransactions: TransactionsService['getTransactions'] = () => {
        return Promise.resolve({
            total: 3,
            totalMatched: 3,
            nextPage: {
                skip: 0,
                limit: 10,
            },
            transactions: [
                {
                    credits: 23,
                    workspaceId: 'workspace_id_123',
                    projectId: 'project_id_784',
                    serviceName: CreditServiceName.TRAINING,
                    millisecondsTimestamp: 1711312113376,
                },
                {
                    credits: 10,
                    workspaceId: 'workspace_id_123',
                    projectId: 'project_id_123',
                    serviceName: CreditServiceName.TRAINING,
                    millisecondsTimestamp: 1711612313376,
                },
                {
                    credits: 17,
                    workspaceId: 'workspace_id_123',
                    projectId: 'project_id_123',
                    serviceName: CreditServiceName.OPTIMIZATION,
                    millisecondsTimestamp: 1711976333245,
                },
            ],
        });
    };

    const getTransactionsAggregates: TransactionsService['getTransactionsAggregates'] = (
        _organizationId,
        queryOptions
    ) => {
        if (
            queryOptions.keys.has(TransactionsAggregatesKey.PROJECT) &&
            queryOptions.keys.has(TransactionsAggregatesKey.SERVICE_NAME)
        ) {
            return Promise.resolve({
                total: 4,
                totalMatched: 4,
                nextPage: {
                    skip: 0,
                    limit: 10,
                },
                aggregates: [
                    {
                        group: [
                            {
                                key: TransactionsAggregatesKey.PROJECT,
                                value: 'test-project1',
                            },
                            {
                                key: TransactionsAggregatesKey.SERVICE_NAME,
                                value: 'training',
                            },
                        ],
                        result: {
                            credits: 10,
                            resources: {
                                images: 10,
                            },
                        },
                    },
                    {
                        group: [
                            {
                                key: TransactionsAggregatesKey.PROJECT,
                                value: 'test-project1',
                            },
                            {
                                key: TransactionsAggregatesKey.SERVICE_NAME,
                                value: 'optimization',
                            },
                        ],
                        result: {
                            credits: 17,
                            resources: {
                                images: 17,
                            },
                        },
                    },
                    {
                        group: [
                            {
                                key: TransactionsAggregatesKey.PROJECT,
                                value: 'test-project2',
                            },
                            {
                                key: TransactionsAggregatesKey.SERVICE_NAME,
                                value: 'training',
                            },
                        ],
                        result: {
                            credits: 23,
                            resources: {
                                frames: 23,
                            },
                        },
                    },
                    {
                        group: [
                            {
                                key: TransactionsAggregatesKey.PROJECT,
                                value: 'test-project2',
                            },
                            {
                                key: TransactionsAggregatesKey.SERVICE_NAME,
                                value: 'optimization',
                            },
                        ],
                        result: {
                            credits: 20,
                            resources: {
                                frames: 20,
                            },
                        },
                    },
                ],
            });
        }
        return Promise.resolve({
            total: 2,
            totalMatched: 2,
            nextPage: {
                skip: 0,
                limit: 10,
            },
            aggregates: [
                {
                    group: [
                        {
                            key: TransactionsAggregatesKey.PROJECT,
                            value: 'test-project1',
                        },
                    ],
                    result: {
                        credits: 27,
                        resources: {
                            images: 27,
                        },
                    },
                },
                {
                    group: [
                        {
                            key: TransactionsAggregatesKey.PROJECT,
                            value: 'test-project2',
                        },
                    ],
                    result: {
                        credits: 53,
                        resources: {
                            frames: 53,
                        },
                    },
                },
            ],
        });
    };

    return {
        getTransactions,
        getTransactionsAggregates,
    };
};
