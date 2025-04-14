// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { createInMemoryProductsService } from '../../../../core/credits/products/services/in-memory-products-service';
import { getMockedPolicy, getMockedProduct } from '../../../../test-utils/mocked-items-factory/mocked-product';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { RenewableAmount } from './renewable-amount.component';

describe('RenewableAmount', () => {
    const renderApp = (productPolicy = getMockedPolicy({ accountName: 'welcoming credits' })) => {
        const productsService = createInMemoryProductsService();
        productsService.getProducts = async () => {
            return {
                total: 2,
                totalMatched: 2,
                nextPage: { limit: 10, skip: 0 },
                products: [getMockedProduct({ productPolicies: [productPolicy] })],
            };
        };

        render(<RenewableAmount />, { services: { productsService } });
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('loading response', () => {
        renderApp();
        expect(screen.getByLabelText('Loading...')).toBeInTheDocument();
    });

    it('render recurring credits', async () => {
        const mockedPolicy = getMockedPolicy({ accountName: 'recurring credits', renewableAmount: 20 });
        renderApp(mockedPolicy);

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        expect(screen.getByText(new RegExp(`${mockedPolicy.renewableAmount} new credits`))).toBeVisible();
    });

    it('recurring credits is not available', async () => {
        const mockedPolicy = getMockedPolicy({ accountName: 'welcoming', renewableAmount: null });
        renderApp(mockedPolicy);

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        expect(screen.queryByText(new RegExp(`${mockedPolicy.renewableAmount} new credits`))).not.toBeInTheDocument();
    });
});
