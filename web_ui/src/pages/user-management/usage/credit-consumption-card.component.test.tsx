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

import { CreditAccount, OrganizationBalance } from '../../../core/credits/credits.interface';
import { createInMemoryCreditsService } from '../../../core/credits/services/in-memory-credits-service';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { CreditConsumptionCard } from './credit-consumption-card.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
    }),
}));

const renderApp = ({
    balance,
    renewableAmounts,
}: {
    balance: OrganizationBalance;
    renewableAmounts: (number | null)[];
}) => {
    const creditsService = createInMemoryCreditsService();
    creditsService.getOrganizationBalance = () => Promise.resolve(balance);
    creditsService.getCreditAccounts = () =>
        Promise.resolve({
            creditAccounts: renewableAmounts.map((amount) => ({ renewableAmount: amount })) as CreditAccount[],
            totalMatchedCount: renewableAmounts.length,
            totalCount: renewableAmounts.length,
            nextPage: null,
        });

    return render(<CreditConsumptionCard />, { services: { creditsService } });
};

describe('CreditsConsumptionCard', () => {
    test('Should render the card with proper content', async () => {
        const balance = { incoming: 100, available: 30, blocked: 10 };
        const renewableAmounts = [20, null, 30, null];
        renderApp({ balance, renewableAmounts });

        await waitFor(async () => {
            expect(await screen.findByTestId('credits-limit-card-renewable-credits-text')).toHaveTextContent(
                'Monthly renewal of 50 credits'
            );
        });
        expect(screen.getByTestId('credits-limit-card-available-credits-chart-label-text')).toHaveTextContent(
            `${balance.available}`
        );
        expect(screen.getByTestId('credits-limit-card-total-credits-chart-label-text')).toHaveTextContent(
            `of ${balance.incoming}`
        );
        expect(screen.getByTestId('credits-limit-card-chart-legend-available-credits-text')).toHaveTextContent('30%');
        expect(screen.getByTestId('credits-limit-card-chart-legend-pending-credits-text')).toHaveTextContent('10%');
    });
});
