// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Product, ProductsResponse } from '../products.interface';

export interface GetProductsQueryOptions {
    skip?: number;
    limit?: number;
}

export interface ProductsService {
    getProducts: (queryOptions: GetProductsQueryOptions) => Promise<ProductsResponse>;
    getProduct: (productId: number) => Promise<Product>;
}
