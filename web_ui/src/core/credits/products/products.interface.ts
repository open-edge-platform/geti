// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { InfiniteQuery } from '../../shared/infinite-query.interface';

export interface ProductPolicy {
    initAmount: number;
    expiresIn: null | number;
    accountName: string;
    renewableAmount: null | number;
}
export interface Product {
    id: number;
    name: string;
    created: number;
    updated: number;
    productPolicies: ProductPolicy[];
}

export interface ProductsResponse extends Omit<InfiniteQuery, 'totalCount'> {
    products: Product[];
    total: number;
    totalMatched: number;
}
