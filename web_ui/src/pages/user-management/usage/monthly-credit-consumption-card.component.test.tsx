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

import { screen, waitFor } from '@testing-library/react';

import { createInMemoryTransactionsService } from '../../../core/credits/transactions/services/in-memory-transactions-service';
import { TransactionsAggregate } from '../../../core/credits/transactions/transactions.interface';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { MonthlyCreditConsumptionCard } from './monthly-credit-consumption-card.component';

const renderApp = ({ aggregates }: { aggregates?: TransactionsAggregate[] }) => {
    const transactionsService = createInMemoryTransactionsService();
    if (aggregates !== undefined) {
        transactionsService.getTransactionsAggregates = () =>
            Promise.resolve({
                total: aggregates.length,
                totalMatched: aggregates.length,
                nextPage: null,
                aggregates,
            });
    }

    return render(<MonthlyCreditConsumptionCard />, { services: { transactionsService } });
};

describe('MonthlyCreditsConsumptionCard', () => {
    test('Should render the card with proper content', async () => {
        renderApp({});

        await waitFor(async () => {
            expect(await screen.findByTestId('monthly-credits-usage-card-credits-count')).toHaveTextContent(
                '80 credits'
            );
        });
        expect(screen.getByTestId('monthly-credits-usage-card-projects-count')).toHaveTextContent('2 projects');
        expect(screen.getByTestId('monthly-credits-usage-card-images-count')).toHaveTextContent('27 images');
    });
});
