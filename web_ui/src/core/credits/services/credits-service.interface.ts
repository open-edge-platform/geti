// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { OrganizationIdentifier } from '../../organizations/organizations.interface';
import {
    CreditAccount,
    CreditAccountIdentifier,
    CreditAccountsResponse,
    NewCreditAccount,
    NewCreditAccountBalance,
    OrganizationBalance,
} from '../credits.interface';

export interface GetCreditAccountsQueryOptions {
    skip?: number;
    limit?: number;
}

export interface CreditsService {
    getOrganizationBalance: (id: OrganizationIdentifier) => Promise<OrganizationBalance>;
    getCreditAccounts: (
        orgId: OrganizationIdentifier,
        queryOptions: GetCreditAccountsQueryOptions
    ) => Promise<CreditAccountsResponse>;
    getCreditAccount: (creditAccountId: CreditAccountIdentifier) => Promise<CreditAccount>;
    createCreditAccount: (creditAccount: NewCreditAccount) => Promise<void>;
    updateCreditAccount: (id: CreditAccountIdentifier, creditAccount: NewCreditAccount) => Promise<CreditAccount>;
    updateCreditAccountBalance: (id: CreditAccountIdentifier, balance: NewCreditAccountBalance) => Promise<void>;
}
