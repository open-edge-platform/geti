// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    TransactionsAggregate,
    TransactionsAggregatesKey,
} from '../../../core/credits/transactions/transactions.interface';
import {
    convertAggregatesToProjectsChartData,
    convertAggregatesToTimeChartData,
    getServiceNamesFromAggregates,
} from './graph-utils';

const aggregates: TransactionsAggregate[] = [
    {
        group: [
            { key: TransactionsAggregatesKey.PROJECT, value: 'project_1' },
            { key: TransactionsAggregatesKey.SERVICE_NAME, value: 'training' },
        ],
        projectName: 'project 1',
        result: {
            credits: 35,
            resources: {},
        },
    },
    {
        group: [
            { key: TransactionsAggregatesKey.PROJECT, value: 'project_1' },
            { key: TransactionsAggregatesKey.SERVICE_NAME, value: 'optimization' },
        ],
        projectName: 'project 1',
        result: {
            credits: 15,
            resources: {},
        },
    },
    {
        group: [
            { key: TransactionsAggregatesKey.PROJECT, value: 'project_2' },
            { key: TransactionsAggregatesKey.SERVICE_NAME, value: 'training' },
        ],
        projectName: 'project 2',
        result: {
            credits: 25,
            resources: {},
        },
    },
    {
        group: [
            { key: TransactionsAggregatesKey.PROJECT, value: 'project_2' },
            { key: TransactionsAggregatesKey.SERVICE_NAME, value: 'optimization' },
        ],
        projectName: 'project 2',
        result: {
            credits: 5,
            resources: {},
        },
    },
];

describe('Graph Utils', () => {
    describe('convertAggregatesToProjectsChartData', () => {
        it('should return empty array if no aggregates are passed', () => {
            const result = convertAggregatesToProjectsChartData(undefined, ['test']);
            expect(result).toEqual([]);
        });

        it('should return proper chartData', () => {
            expect(convertAggregatesToProjectsChartData(aggregates, ['training', 'optimization'])).toEqual([
                {
                    label: 'project 1',
                    values: {
                        training: 35,
                        optimization: 15,
                    },
                },
                {
                    label: 'project 2',
                    values: {
                        training: 25,
                        optimization: 5,
                    },
                },
            ]);
        });
    });

    describe('convertAggregatesToTimeChartData', () => {
        it('should return empty array if no aggregates are passed', () => {
            const result = convertAggregatesToTimeChartData(undefined, ['test']);
            expect(result).toEqual([]);
        });

        it('should return proper result', () => {
            const timeAggregates: TransactionsAggregate[] = [
                {
                    group: [
                        { key: TransactionsAggregatesKey.SERVICE_NAME, value: 'training' },
                        { key: TransactionsAggregatesKey.DATE, value: 1 },
                    ],
                    result: {
                        credits: 35,
                        resources: {},
                    },
                },
                {
                    group: [
                        { key: TransactionsAggregatesKey.SERVICE_NAME, value: 'training' },
                        { key: TransactionsAggregatesKey.DATE, value: 2 },
                    ],
                    result: {
                        credits: 15,
                        resources: {},
                    },
                },
                {
                    group: [
                        { key: TransactionsAggregatesKey.SERVICE_NAME, value: 'optimization' },
                        { key: TransactionsAggregatesKey.DATE, value: 2 },
                    ],
                    result: {
                        credits: 25,
                        resources: {},
                    },
                },
                {
                    group: [
                        { key: TransactionsAggregatesKey.SERVICE_NAME, value: 'optimization' },
                        { key: TransactionsAggregatesKey.DATE, value: 3 },
                    ],
                    result: {
                        credits: 5,
                        resources: {},
                    },
                },
            ];
            expect(convertAggregatesToTimeChartData(timeAggregates, ['training', 'optimization'])).toEqual([
                {
                    label: 1,
                    values: {
                        training: 35,
                        optimization: 0,
                    },
                },
                {
                    label: 2,
                    values: {
                        training: 15,
                        optimization: 25,
                    },
                },
                {
                    label: 3,
                    values: {
                        training: 0,
                        optimization: 5,
                    },
                },
            ]);
        });
    });

    describe('getServiceNamesFromAggregates', () => {
        it('should return empty array if no aggregates are passed', () => {
            const result = getServiceNamesFromAggregates();
            expect(result).toEqual([]);
        });
        it('should return proper array with service names', () => {
            expect(getServiceNamesFromAggregates(aggregates)).toEqual(['training', 'optimization']);
        });
    });
});
