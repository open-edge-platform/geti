// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { InfiniteQuery } from '../shared/infinite-query.interface';

export const CREDIT_COST_PER_IMAGE_OR_VIDEO = 1;

export interface OrganizationBalance {
    incoming: number;
    available: number;
    blocked: number;
}

export interface CreditAccountIdentifier {
    organizationId: string;
    creditAccountId: string;
}

export interface CreditAccountBalance {
    incoming: number;
    available: number;
    blocked: number;
}

interface CommonCreditAccount {
    id: string;
    organizationId: string;
    name: string;
    balance: CreditAccountBalance;
    createdAt: number;
    updatedAt: number;
    expires: number | null;
}

export interface RenewableCreditAccount extends CommonCreditAccount {
    type: 'renewable';
    renewalDayOfMonth: number;
    renewableAmount: number;
}

export interface NonRenewableCreditAccount extends CommonCreditAccount {
    type: 'non-renewable';
    renewableAmount: undefined;
    renewalDayOfMonth: undefined;
}

export type CreditAccount = RenewableCreditAccount | NonRenewableCreditAccount;

export interface CreditAccountsResponse extends InfiniteQuery {
    creditAccounts: CreditAccount[];
    totalMatchedCount: number;
}

export interface NewCreditAccount {
    organizationId: string;
    name: string;
    initAmount?: number;
    expires?: number;
    renewableAmount?: number;
    renewalDayOfMonth?: number;
}

export interface NewCreditAccountBalance {
    add?: number;
    subtract?: number;
}
