// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { Flex } from '@adobe/react-spectrum';
import { StyleProps } from '@react-types/shared';

import { useTransactionsQueries } from '../../../core/credits/transactions/hooks/use-transactions.hook';
import {
    TransactionsAggregatesGroupItem,
    TransactionsAggregatesKey,
} from '../../../core/credits/transactions/transactions.interface';
import { useFirstWorkspaceIdentifier } from '../../../providers/workspaces-provider/use-first-workspace-identifier.hook';
import { TextWithLabel } from '../../../shared/components/text-with-label/text-with-label.component';
import { pluralize } from '../../../shared/utils';

export const MonthlyCreditConsumptionCard = (props: StyleProps): JSX.Element => {
    const { useGetTransactionsAggregates } = useTransactionsQueries();
    const { organizationId, workspaceId } = useFirstWorkspaceIdentifier();
    const { data } = useGetTransactionsAggregates(
        { workspaceId, organizationId },
        {
            keys: new Set([TransactionsAggregatesKey.PROJECT]),
        }
    );

    const projectsCount = useMemo(
        () =>
            data?.aggregates.reduce((acc, curr) => {
                curr.group.map((group) => {
                    if (group.key === TransactionsAggregatesKey.PROJECT) {
                        return acc.add(group.value);
                    }
                });
                return acc;
            }, new Set<TransactionsAggregatesGroupItem['value']>()).size || 0,
        [data]
    );

    const creditsCount = useMemo(
        () => data?.aggregates.reduce((acc, curr) => acc + curr.result.credits, 0) || 0,
        [data]
    );
    const imagesCount = useMemo(
        () => data?.aggregates.reduce((acc, curr) => acc + (curr.result.resources?.images || 0), 0) || 0,
        [data]
    );

    return (
        <Flex justifyContent={'space-between'} {...props}>
            <TextWithLabel
                label='Credits'
                data-testid='monthly-credits-usage-card-credits-count'
                id='monthly-credits-usage-card-credits-count'
            >
                {pluralize(creditsCount, 'credit')}
            </TextWithLabel>
            <TextWithLabel
                label='Projects'
                data-testid='monthly-credits-usage-card-projects-count'
                id='monthly-credits-usage-card-projects-count'
            >
                {pluralize(projectsCount, 'project')}
            </TextWithLabel>
            <TextWithLabel
                label='Images'
                data-testid='monthly-credits-usage-card-images-count'
                id='monthly-credits-usage-card-images-count'
            >
                {pluralize(imagesCount, 'image')}
            </TextWithLabel>
        </Flex>
    );
};
