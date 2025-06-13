// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Loading, Text } from '@geti/ui';

import { useProducts } from '../../../../core/credits/products/hooks/use-products.hook';
import { findPolicy, hasRenewableAmount } from '../../../../core/credits/products/hooks/utils';
import { getSingularOrPluralDays, remainingDaysUntilNextMonth } from './util';

import classes from './credit-balance.module.scss';

//TODO: remove if not longer needed for credit system
export const RenewableAmount = () => {
    const { useGetProductsQuery } = useProducts();
    const { data: productsResponse, isFetching } = useGetProductsQuery();

    const remainingDays = remainingDaysUntilNextMonth();
    const recurringCredits = findPolicy(productsResponse?.products, hasRenewableAmount);

    if (isFetching) {
        return <Loading mode='inline' size={'S'} style={{ height: 'initial' }} />;
    }

    if (!recurringCredits?.renewableAmount) {
        return null;
    }

    return (
        <Text UNSAFE_className={classes.remainingDay}>
            {recurringCredits.renewableAmount} new credits in {remainingDays} {getSingularOrPluralDays(remainingDays)}
        </Text>
    );
};
