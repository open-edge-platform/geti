// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

import { createInMemoryTransactionsService } from '../../../core/credits/transactions/services/in-memory-transactions-service';
import { CreditServiceName, Transaction } from '../../../core/credits/transactions/transactions.interface';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { CreditConsumptionRecords } from './credit-consumption-records.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace_1',
    }),
}));

const getMockedTransaction = (transaction: Partial<Transaction> = {}): Transaction => ({
    credits: 10,
    workspaceId: 'workspace-id-1',
    projectId: 'project-id-1',
    serviceName: CreditServiceName.TRAINING,
    millisecondsTimestamp: new Date('2024-01-01').valueOf(),
    ...transaction,
});

const selectTodayDate = async () => {
    fireEvent.click(screen.getByLabelText('Calendar'));

    //click twice to select from-to-date
    fireEvent.click(await screen.findByRole('button', { name: /today/i }));
    fireEvent.click(await screen.findByRole('button', { name: /today/i }));
};

const renderApp = async ({
    transactions,
    mockedGetTransactions = jest.fn(),
}: {
    transactions?: Transaction[];
    mockedGetTransactions?: jest.Mock;
}) => {
    const transactionsService = createInMemoryTransactionsService();

    if (transactions !== undefined) {
        transactionsService.getTransactions = mockedGetTransactions.mockResolvedValue({
            total: transactions.length,
            totalMatched: transactions.length,
            nextPage: null,
            transactions,
        });
    }

    const container = render(<CreditConsumptionRecords />, { services: { transactionsService } });

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    return container;
};

describe('CreditConsumptionRecords', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('show NotFound illustrated message', async () => {
        await renderApp({ transactions: [] });

        expect(screen.getByText('No results')).toBeVisible();
    });

    test('date restore updates transactions query', async () => {
        const mockedGetTransactions = jest.fn();
        await renderApp({ transactions: [], mockedGetTransactions });

        await selectTodayDate();
        mockedGetTransactions.mockClear();

        fireEvent.click(screen.getByRole('button', { name: /reset calendar/i }));

        await waitFor(() => {
            expect(mockedGetTransactions).toHaveBeenCalledWith(expect.any(Object), {
                toDate: undefined,
                fromDate: undefined,
                limit: expect.any(Number),
            });
        });
    });

    test('date selection updates transactions query', async () => {
        const mockedGetTransactions = jest.fn();
        const today = new Date(new Date().setHours(0, 0, 0, 0));
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        await renderApp({ transactions: [], mockedGetTransactions });

        mockedGetTransactions.mockClear();

        await selectTodayDate();

        await waitFor(() => {
            expect(mockedGetTransactions).toHaveBeenCalledWith(expect.any(Object), {
                fromDate: `${today.valueOf()}`,
                toDate: `${tomorrow.valueOf()}`,
                limit: expect.any(Number),
            });
        });
    });

    test('render aggregated row', async () => {
        await renderApp({ transactions: [getMockedTransaction()] });

        expect(screen.getByLabelText('table consumption by records')).toBeVisible();

        //Header row + 1 aggregated row
        expect(screen.getAllByRole('row')).toHaveLength(2);
    });
});
