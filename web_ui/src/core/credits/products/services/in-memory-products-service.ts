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
