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

import { Text, View } from '@adobe/react-spectrum';

import { CreditAccount } from '../../../../core/credits/credits.interface';
import { ordinalSuffixOf } from '../../../../shared/utils';

import classes from '../organization.module.scss';

interface RenewalDayCellProps {
    rowData: CreditAccount;
}

export const RenewalDayCell = ({ rowData }: RenewalDayCellProps): JSX.Element => {
    if (typeof rowData.renewalDayOfMonth !== 'number') {
        return <Text>No</Text>;
    }

    return (
        <View>
            <Text>
                {rowData.renewableAmount} {rowData.renewableAmount === 1 ? 'credit' : 'credits'} / Monthly
            </Text>
            <br />
            <Text UNSAFE_className={classes.tableCellSecondaryText}>
                Starting {rowData.renewalDayOfMonth}
                {ordinalSuffixOf(rowData.renewalDayOfMonth)}
            </Text>
        </View>
    );
};
