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

import { Text } from '@adobe/react-spectrum';

import { useProducts } from '../../../../core/credits/products/hooks/use-products.hook';
import { findPolicy, hasRenewableAmount } from '../../../../core/credits/products/hooks/utils';
import { LoadingIndicator } from '../../loading/loading-indicator.component';
import { getSingularOrPluralDays, remainingDaysUntilNextMonth } from './util';

import classes from './credit-balance.module.scss';

//TODO: remove if not longer needed for credit system
export const RenewableAmount = () => {
    const { useGetProductsQuery } = useProducts();
    const { data: productsResponse, isFetching } = useGetProductsQuery();

    const remainingDays = remainingDaysUntilNextMonth();
    const recurringCredits = findPolicy(productsResponse?.products, hasRenewableAmount);

    if (isFetching) {
        return <LoadingIndicator size={'S'} height={'initial'} />;
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
