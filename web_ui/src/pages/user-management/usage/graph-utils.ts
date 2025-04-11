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

import get from 'lodash/get';
import isEmpty from 'lodash/isEmpty';

import {
    TransactionsAggregate,
    TransactionsAggregatesKey,
} from '../../../core/credits/transactions/transactions.interface';

const COLORS = {
    training: '#8BAE46',
    optimization: '#FEC91B',
};

export const getColorFromServiceName = (serviceName: string): string => {
    return get(COLORS, serviceName, '#00c7fd');
};

interface AggregateChartData {
    label: number | string;
    values: { [key: string]: number };
}

export const convertAggregatesToProjectsChartData = (
    aggregates: TransactionsAggregate[] = [],
    serviceNames: string[]
): AggregateChartData[] => {
    const projectsData: { [key: string]: AggregateChartData } = {};

    aggregates.forEach((aggregate) => {
        const projectId = aggregate.group.find((group) => group.key === TransactionsAggregatesKey.PROJECT)?.value;
        const serviceName = aggregate.group.find(
            (group) => group.key === TransactionsAggregatesKey.SERVICE_NAME
        )?.value;

        if (!projectId) return;

        if (isEmpty(projectsData[projectId])) {
            projectsData[projectId] = {
                label: aggregate.projectName || '',
                values: Object.fromEntries(serviceNames.map((name) => [name, 0])),
            };
        }

        if (!serviceName) return;

        projectsData[projectId].values[serviceName] = aggregate.result.credits;
    });

    return Object.values(projectsData);
};

export const convertAggregatesToTimeChartData = (
    aggregates: TransactionsAggregate[] = [],
    serviceNames: string[]
): AggregateChartData[] => {
    const timeData: { [key: number]: AggregateChartData } = {};

    if (isEmpty(serviceNames)) return [];

    aggregates.forEach((aggregate) => {
        const date = aggregate.group.find((group) => group.key === TransactionsAggregatesKey.DATE)?.value as
            | number
            | undefined;
        const serviceName = aggregate.group.find(
            (group) => group.key === TransactionsAggregatesKey.SERVICE_NAME
        )?.value;

        if (!date) return;

        if (isEmpty(timeData[date])) {
            timeData[date] = {
                label: date,
                values: Object.fromEntries(serviceNames.map((name) => [name, 0])),
            };
        }

        if (!serviceName) return;

        timeData[date].values[serviceName] = aggregate.result.credits || 0;
    });

    return Object.values(timeData);
};

export const getServiceNamesFromAggregates = (aggregates: TransactionsAggregate[] = []): string[] =>
    Array.from(
        new Set(
            aggregates.flatMap(
                (aggregate) =>
                    aggregate.group
                        .map((group) =>
                            group.key === TransactionsAggregatesKey.SERVICE_NAME ? group.value : undefined
                        )
                        .filter((v) => v) as string[]
            )
        )
    );
