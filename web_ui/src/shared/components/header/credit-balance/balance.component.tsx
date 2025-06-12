// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Loading, useNumberFormatter } from '@geti/ui';
import { isNil } from 'lodash-es';

import { OrganizationBalance } from '../../../../core/credits/credits.interface';

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
        return <Loading mode='inline' size={'S'} style={{ height: 'initial' }} />;
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
