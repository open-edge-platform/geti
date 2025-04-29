// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

interface ProductPolicyDTO {
    account_name: string;
    init_amount: number;
    renewable_amount: null | number;
    expires_in: null | number;
}

export interface ProductDTO {
    id: number;
    name: string;
    created: number;
    updated: number;
    product_policies: ProductPolicyDTO[];
}

export interface ProductsResponseDTO {
    products: ProductDTO[];
    total: number;
    total_matched: number;
    next_page: {
        skip: number;
        limit: number;
    };
}
