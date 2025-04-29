// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
