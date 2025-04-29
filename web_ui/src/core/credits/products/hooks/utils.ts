// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Product, ProductPolicy } from '../products.interface';

export const hasWelcomingCredits = ({ initAmount }: ProductPolicy) => Number.isFinite(initAmount);
export const hasRenewableAmount = ({ renewableAmount }: ProductPolicy) => Number.isFinite(renewableAmount);

export const findPolicy = (products: Product[] | undefined, predicate: (policy: ProductPolicy) => boolean) => {
    return products?.flatMap(({ productPolicies }) => productPolicies)?.find(predicate);
};
