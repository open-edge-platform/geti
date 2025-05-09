// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { groupBy, isEmpty } from 'lodash-es';

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
