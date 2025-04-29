// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedPolicy, getMockedProduct } from '../../../../test-utils/mocked-items-factory/mocked-product';
import { ProductsService } from './products-service.interface';

export const createInMemoryProductsService = (): ProductsService => {
    const getProducts: ProductsService['getProducts'] = async () => {
        return Promise.resolve({
            total: 2,
            totalMatched: 2,
            nextPage: {
                limit: 10,
                skip: 0,
            },
            products: [
                getMockedProduct({
                    id: 123,
                    name: 'Free Tier STUB',
                    productPolicies: [
                        getMockedPolicy({ accountName: 'welcoming credits', initAmount: 20 }),
                        getMockedPolicy({ accountName: 'recurring credits', initAmount: 0, expiresIn: null }),
                    ],
                }),
            ],
        });
    };

    const getProduct: ProductsService['getProduct'] = async (_productId) => {
        return getMockedProduct({
            id: 123,
            name: 'Free Tier STUB',
            productPolicies: [
                getMockedPolicy({ accountName: 'welcoming credits', initAmount: 20 }),
                getMockedPolicy({ accountName: 'recurring credits', initAmount: 0, expiresIn: null }),
            ],
        });
    };

    return {
        getProducts,
        getProduct,
    };
};
