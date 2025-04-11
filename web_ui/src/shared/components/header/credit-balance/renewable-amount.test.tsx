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
