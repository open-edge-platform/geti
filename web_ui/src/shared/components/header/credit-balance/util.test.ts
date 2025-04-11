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

import { CreditServiceName } from '../../../../core/credits/transactions/transactions.interface';
import { getMockedTransaction } from '../../../../test-utils/mocked-items-factory/mocked-transactions';
import { CREDIT_LOW_LIMIT, getClassServiceName, getProjectName, getSingularOrPluralDays, isBalanceLow } from './util';

describe('credit-balance util', () => {
    it('isBalanceLow', () => {
        expect(isBalanceLow({ available: 0, incoming: 0, blocked: 0 })).toBe(true);
        expect(isBalanceLow({ available: 1, incoming: 0, blocked: 0 })).toBe(true);
        expect(isBalanceLow({ available: CREDIT_LOW_LIMIT, incoming: 0, blocked: 0 })).toBe(false);
        expect(isBalanceLow({ available: CREDIT_LOW_LIMIT + 1, incoming: 0, blocked: 0 })).toBe(false);
        expect(isBalanceLow({ available: CREDIT_LOW_LIMIT - 1, incoming: 0, blocked: 0 })).toBe(true);
    });

    it('getSingularOrPluralDays', () => {
        expect(getSingularOrPluralDays(1)).toBe('day');
        expect(getSingularOrPluralDays(2)).toBe('days');
        expect(getSingularOrPluralDays(10)).toBe('days');
    });

    it('getProjectName', () => {
        const projectId = '123';
        const projectName = 'name-test';
        expect(getProjectName(getMockedTransaction({ projectId }))).toBe(`Unknown project - ${projectId}`);
        expect(getProjectName(getMockedTransaction({ projectName }))).toBe(projectName);
    });

    it('getClassServiceName', () => {
        expect(getClassServiceName(CreditServiceName.TRAINING)).toBe(`greenTitle`);
        expect(getClassServiceName(CreditServiceName.OPTIMIZATION)).toBe(`yellowTitle`);
    });
});
