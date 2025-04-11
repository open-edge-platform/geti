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

import {
    getMockedNonRenewableCreditAccount,
    getMockedRenewableCreditAccount,
} from '../../../test-utils/mocked-items-factory/mocked-credit-accounts';
import { CreditsService } from './credits-service.interface';

export const createInMemoryCreditsService = (): CreditsService => {
    const getOrganizationBalance: CreditsService['getOrganizationBalance'] = () => {
        return Promise.resolve({
            incoming: 100,
            available: 200,
            blocked: 50,
        });
    };

    const getCreditAccounts: CreditsService['getCreditAccounts'] = ({ organizationId }) => {
        return Promise.resolve({
            creditAccounts: [
                getMockedNonRenewableCreditAccount({ organizationId }),
                getMockedRenewableCreditAccount({ organizationId }),
            ],
            totalCount: 2,
            totalMatchedCount: 2,
            nextPage: {
                skip: 0,
                limit: 10,
            },
        });
    };

    const getCreditAccount: CreditsService['getCreditAccount'] = ({ organizationId }) => {
        return Promise.resolve(getMockedNonRenewableCreditAccount({ organizationId }));
    };

    const createCreditAccount: CreditsService['createCreditAccount'] = () => {
        return Promise.resolve();
    };

    const updateCreditAccount: CreditsService['updateCreditAccount'] = (id, creditAccount) => {
        const newCreditAccount = {
            id: id.creditAccountId,
            organizationId: creditAccount.organizationId,
            name: creditAccount.name,
            createdAt: 1704063600,
            updatedAt: Date.now(),
            expires: creditAccount.expires ?? null,
            renewableAmount: creditAccount.renewableAmount,
            renewalDayOfMonth: creditAccount.renewalDayOfMonth,
            balance: {
                incoming: creditAccount.initAmount ?? 0,
                available: creditAccount.initAmount ?? 0,
                blocked: 0,
            },
        };
        if (typeof creditAccount.renewableAmount === 'undefined') {
            return Promise.resolve({
                ...newCreditAccount,
                type: 'non-renewable' as const,
                renewableAmount: undefined,
                renewalDayOfMonth: undefined,
            });
        }
        return Promise.resolve({
            ...newCreditAccount,
            type: 'renewable' as const,
            renewableAmount: creditAccount.renewableAmount ?? 500,
            renewalDayOfMonth: creditAccount.renewalDayOfMonth ?? 1,
        });
    };

    const updateCreditAccountBalance: CreditsService['updateCreditAccountBalance'] = () => {
        return Promise.resolve();
    };

    return {
        getOrganizationBalance,
        getCreditAccounts,
        getCreditAccount,
        createCreditAccount,
        updateCreditAccount,
        updateCreditAccountBalance,
    };
};
