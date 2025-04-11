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

import { ProductDTO, ProductsResponseDTO } from '../dtos/products.interface';
import { Product, ProductsResponse } from '../products.interface';
import { GetProductsQueryOptions } from './products-service.interface';

export const getProductEntity = ({ id, product_policies, name, created, updated }: ProductDTO): Product => ({
    id,
    name,
    created,
    updated,
    productPolicies: product_policies.map((policy) => ({
        initAmount: policy.init_amount,
        expiresIn: policy.expires_in,
        accountName: policy.account_name,
        renewableAmount: policy.renewable_amount,
    })),
});

export const getProductsResponseEntity = (productsResponseDTO: ProductsResponseDTO): ProductsResponse => {
    return {
        products: productsResponseDTO.products.map(getProductEntity),
        total: productsResponseDTO.total,
        totalMatched: productsResponseDTO.total_matched,
        nextPage: productsResponseDTO.next_page && {
            skip: productsResponseDTO.next_page.skip,
            limit: productsResponseDTO.next_page.limit,
        },
    };
};

export const getProductsQueryOptionsDTO = ({ skip, limit }: GetProductsQueryOptions): GetProductsQueryOptions => {
    return {
        skip: skip ?? 0,
        limit: limit ?? 10,
    };
};
