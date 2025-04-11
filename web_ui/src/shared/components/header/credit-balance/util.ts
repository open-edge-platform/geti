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

import dayjs from 'dayjs';

import { OrganizationBalance } from '../../../../core/credits/credits.interface';
import { CreditServiceName, Transaction } from '../../../../core/credits/transactions/transactions.interface';

import classes from './credit-balance.module.scss';

export const CREDIT_LOW_LIMIT = 20;

export const isBalanceLow = (organizationBalance: OrganizationBalance) =>
    organizationBalance.available < Math.max(CREDIT_LOW_LIMIT, 0.1 * organizationBalance.incoming);

export const remainingDaysUntilNextMonth = () => {
    const currentDate = dayjs();
    const startOfNextMonth = currentDate.add(1, 'month').startOf('month');
    return startOfNextMonth.diff(currentDate, 'day');
};

export const getSingularOrPluralDays = (days: number) => {
    return days <= 1 ? 'day' : 'days';
};

export const getProjectName = (transaction: Transaction) => {
    return transaction.projectName ? transaction.projectName : `Unknown project - ${transaction.projectId}`;
};

export const getClassServiceName = (name: CreditServiceName) =>
    name === CreditServiceName.OPTIMIZATION ? classes.yellowTitle : classes.greenTitle;
