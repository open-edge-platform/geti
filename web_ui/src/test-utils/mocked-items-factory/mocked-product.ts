// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Product, ProductPolicy } from '../../core/credits/products/products.interface';

export const getMockedPolicy = (policy: Partial<ProductPolicy> = {}): ProductPolicy => {
    return {
        accountName: 'welcoming credits',
        initAmount: 1000,
        renewableAmount: null,
        expiresIn: 99999,
        ...policy,
    };
};

export const getMockedProduct = (product: Partial<Product> = {}): Product => {
    return {
        id: 123,
        name: 'Freemium',
        productPolicies: [
            getMockedPolicy({ accountName: 'welcoming credits', initAmount: 100 }),
            getMockedPolicy({ accountName: 'recurring credits', renewableAmount: 120 }),
        ],
        created: 1711113382958,
        updated: 1711113382958,
        ...product,
    };
};
