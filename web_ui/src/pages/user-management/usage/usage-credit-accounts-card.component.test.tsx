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

import { screen, waitFor, within } from '@testing-library/react';

import { CreditAccount } from '../../../core/credits/credits.interface';
import { createInMemoryCreditsService } from '../../../core/credits/services/in-memory-credits-service';
import {
    getMockedNonRenewableCreditAccount,
    getMockedRenewableCreditAccount,
} from '../../../test-utils/mocked-items-factory/mocked-credit-accounts';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { UsageCreditAccountsCard } from './usage-credit-accounts-card.component';

const renderApp = async ({ creditAccounts }: { creditAccounts: CreditAccount[] }) => {
    const creditsService = createInMemoryCreditsService();
    creditsService.getCreditAccounts = () =>
        Promise.resolve({
            creditAccounts,
            totalMatchedCount: creditAccounts.length,
            totalCount: creditAccounts.length,
            nextPage: null,
        });

    return render(<UsageCreditAccountsCard />, { services: { creditsService } });
};

describe('Usage', () => {
    test('Should render only two rows in table with "show more" button', async () => {
        await renderApp({
            creditAccounts: [
                getMockedNonRenewableCreditAccount({ id: '1' }),
                getMockedRenewableCreditAccount({ id: '2' }),
                getMockedNonRenewableCreditAccount({ id: '3' }),
            ],
        });

        expect(await screen.findByRole('link', { name: 'Show all credit accounts' })).toBeInTheDocument();
        await waitFor(() => {
            expect(within(screen.getAllByRole('rowgroup')[1]).getAllByRole('row')).toHaveLength(2);
        });
    });

    test('Should render one row without "show more" button', async () => {
        await renderApp({
            creditAccounts: [getMockedNonRenewableCreditAccount()],
        });

        expect(screen.queryByRole('link', { name: 'Show all credit accounts' })).not.toBeInTheDocument();
        await waitFor(() => {
            expect(within(screen.getAllByRole('rowgroup')[1]).getAllByRole('row')).toHaveLength(1);
        });
    });
});
