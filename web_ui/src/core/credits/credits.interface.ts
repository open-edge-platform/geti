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
