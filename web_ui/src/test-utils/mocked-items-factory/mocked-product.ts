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
