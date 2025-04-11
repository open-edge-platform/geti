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
