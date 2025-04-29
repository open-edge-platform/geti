// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export const productsPolicy = {
    total_matched: 0,
    next_page: { limit: 0, skip: 0 },
    products: [
        {
            id: 123,
            name: 'test-1',
            product_policies: [
                {
                    account_name: 'test-1',
                    init_amount: 1000,
                    renewable_amount: 0,
                    expires_in: 0,
                },
            ],
            created: Date.now(),
            updated: Date.now(),
        },
    ],
};
