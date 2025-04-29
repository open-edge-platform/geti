// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { v4 as uuid } from 'uuid';

import { CreditAccount, NonRenewableCreditAccount, RenewableCreditAccount } from '../../core/credits/credits.interface';
import { CreditAccountDTO } from '../../core/credits/dtos/credits.interface';

export const getMockedRenewableCreditAccount = (creditAccount: Partial<RenewableCreditAccount> = {}): CreditAccount => {
    return {
        id: uuid(),
        name: 'Freemium Account',
        type: 'renewable' as const,
        organizationId: 'organization-id',
        renewableAmount: 100,
        renewalDayOfMonth: 1,
        createdAt: 1704063600000,
        updatedAt: 1704063600000,
        expires: null,
        balance: {
            incoming: 100,
            available: 100,
            blocked: 0,
        },
        ...creditAccount,
    };
};

export const getMockedNonRenewableCreditAccount = (
    creditAccount: Partial<NonRenewableCreditAccount> = {}
): CreditAccount => {
    return {
        id: uuid(),
        name: 'Welcoming Account',
        type: 'non-renewable' as const,
        organizationId: 'organization-id',
        createdAt: 1704063600000,
        updatedAt: 1704063600000,
        expires: 1735686000000,
        balance: {
            incoming: 1000,
            available: 900,
            blocked: 100,
        },
        ...creditAccount,
    };
};

export const getMockedCreditAccountDTO = (creditAccount: Partial<CreditAccountDTO> = {}): CreditAccountDTO => {
    return {
        balance: {
            incoming: 500,
            available: 100,
            blocked: 0,
        },
        created: 1713132000000,
        expires: 1735599600000,
        id: uuid(),
        name: 'Welcoming credits',
        organization_id: 'organization-id-1',
        renewable_amount: null,
        renewal_day_of_month: null,
        updated: 1713132000000,
        ...creditAccount,
    };
};
