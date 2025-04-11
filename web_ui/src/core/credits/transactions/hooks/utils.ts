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

import groupBy from 'lodash/groupBy';
import isEmpty from 'lodash/isEmpty';

import { ProjectName } from '../../../projects/project.interface';
import { Transaction, TransactionsAggregate, TransactionsAggregatesKey } from '../transactions.interface';

export const setTransactionProjectName = (projects: ProjectName[] = [], transactions: Transaction[]): Transaction[] => {
    const groupedById = groupBy(projects, 'id');

    return transactions.map((transaction) => {
        const projectMatch = groupedById[transaction.projectId];
        const projectName = !isEmpty(projectMatch)
            ? projectMatch[0].name
            : `Undefined project - id: ${transaction.projectId}`;

        return { ...transaction, projectName };
    });
};

export const setTransactionAggregatesProjectName = (
    projects: ProjectName[] = [],
    aggregates: TransactionsAggregate[]
): TransactionsAggregate[] => {
    const groupedById = groupBy(projects, 'id');

    return aggregates.map((aggregate) => {
        const projectGroup = aggregate.group.find((group) => group.key === TransactionsAggregatesKey.PROJECT);
        const projectId = projectGroup?.value;
        const projectMatch = projectId ? groupedById[projectId] : [];
        const projectName = !isEmpty(projectMatch) ? projectMatch[0].name : `Undefined project - id: ${projectId}`;

        return { ...aggregate, projectName };
    });
};
