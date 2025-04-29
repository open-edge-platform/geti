// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    CreditAccount,
    CreditAccountBalance,
    CreditAccountsResponse,
    NewCreditAccount,
    OrganizationBalance,
} from '../credits.interface';
import {
    CreditAccountDTO,
    CreditAccountsResponseDTO,
    GetCreditAccountsQueryOptionsDTO,
    NewCreditAccountDTO,
} from '../dtos/credits.interface';
import { GetCreditAccountsQueryOptions } from './credits-service.interface';

export const getCreditAccountEntity = (creditAccount: CreditAccountDTO): CreditAccount => {
    const { id, name, organization_id, renewable_amount, renewal_day_of_month, expires, balance, created, updated } =
        creditAccount;
    if (renewable_amount !== null && renewal_day_of_month !== null) {
        return {
            id,
            name,
            organizationId: organization_id,
            renewableAmount: renewable_amount,
            renewalDayOfMonth: renewal_day_of_month,
            expires,
            balance: {
                incoming: balance.incoming,
                available: balance.available,
                blocked: balance.blocked,
            },
            createdAt: created,
            updatedAt: updated,
            type: 'renewable' as const,
        };
    } else {
        return {
            id,
            name,
            organizationId: organization_id,
            expires,
            renewableAmount: undefined,
            renewalDayOfMonth: undefined,
            balance: {
                incoming: balance.incoming,
                available: balance.available,
                blocked: balance.blocked,
            },
            createdAt: created,
            updatedAt: updated,
            type: 'non-renewable' as const,
        };
    }
};

export const getNewCreditAccountEntityDTO = (creditAccount: NewCreditAccount): NewCreditAccountDTO => {
    return {
        name: creditAccount.name,
        init_amount: creditAccount.initAmount,
        renewable_amount: creditAccount.renewableAmount,
        renewal_day_of_month: creditAccount.renewalDayOfMonth,
        expires: creditAccount.expires,
    };
};

export const getCreditAccountsResponseEntity = (
    creditAccountsResponseDTO: CreditAccountsResponseDTO
): CreditAccountsResponse => {
    return {
        creditAccounts: creditAccountsResponseDTO.credit_accounts.map(getCreditAccountEntity),
        totalCount: creditAccountsResponseDTO.total,
        totalMatchedCount: creditAccountsResponseDTO.total_matched,
        nextPage: creditAccountsResponseDTO.next_page && {
            skip: creditAccountsResponseDTO.next_page.skip,
            limit: creditAccountsResponseDTO.next_page.limit,
        },
    };
};

export const getCreditAccountsQueryOptionsDTO = (
    queryOptions: GetCreditAccountsQueryOptions
): GetCreditAccountsQueryOptionsDTO => {
    return {
        skip: queryOptions.skip ?? 0,
        limit: queryOptions.limit ?? 10,
    };
};

export const getBalanceUsedCredits = (balance: OrganizationBalance | CreditAccountBalance): number => {
    return balance.incoming - balance.available - balance.blocked;
};
