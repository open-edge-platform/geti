// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Text, View } from '@geti/ui';

import { CreditAccount } from '../../../../core/credits/credits.interface';
import { ordinalSuffixOf } from '../../../../shared/utils';

import classes from './credit-accounts-table.module.scss';

interface RenewalDayCellProps {
    rowData: CreditAccount;
}

export const RenewalDayCell = ({ rowData }: RenewalDayCellProps): JSX.Element => {
    if (typeof rowData.renewalDayOfMonth !== 'number') {
        return <Text>No</Text>;
    }

    return (
        <View>
            <Text>{rowData.renewableAmount} / Monthly</Text>
            <br />
            <Text UNSAFE_className={classes.renewalDayCellSecondaryText}>
                Starting {rowData.renewalDayOfMonth}
                {ordinalSuffixOf(rowData.renewalDayOfMonth)}
            </Text>
        </View>
    );
};
