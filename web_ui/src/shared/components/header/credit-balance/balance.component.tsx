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

import { Flex, useNumberFormatter } from '@adobe/react-spectrum';
import isNil from 'lodash/isNil';

import { OrganizationBalance } from '../../../../core/credits/credits.interface';
import { LoadingIndicator } from '../../loading/loading-indicator.component';

import classes from './credit-balance.module.scss';

export const Balance = ({
    isLoading,
    organizationBalance,
}: {
    isLoading: boolean;
    organizationBalance?: OrganizationBalance;
}) => {
    const numberFormatter = useNumberFormatter({});

    if (isLoading) {
        return <LoadingIndicator size={'S'} height={'initial'} />;
    }

    if (isNil(organizationBalance)) {
        return null;
    }

    return (
        <Flex alignItems={'end'}>
            <span aria-label='available' className={classes.creditRemain}>
                {numberFormatter.format(organizationBalance.available)}
            </span>
            {organizationBalance.blocked > 0 && (
                <span aria-label='pending' className={classes.creditPending}>
                    {` (${numberFormatter.format(organizationBalance.blocked)} pending)`}
                </span>
            )}
            <span aria-label='incoming' className={classes.creditIncoming}>
                {' '}
                of {numberFormatter.format(organizationBalance.incoming)}
            </span>
        </Flex>
    );
};
