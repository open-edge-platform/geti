// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
