// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export interface ResponseTotalsDTO {
    total: number;
    total_matched: number;
    next_page: {
        skip: number;
        limit: number;
    } | null;
}

export interface OrganizationBalanceDTO {
    incoming: number;
    available: number;
    blocked: number;
}

export interface GetCreditAccountsQueryOptionsDTO {
    skip: number;
    limit: number;
}

interface CreditAccountBalanceDTO {
    incoming: number;
    available: number;
    blocked: number;
}

export interface CreditAccountDTO {
    id: string;
    organization_id: string;
    name: string;
    balance: CreditAccountBalanceDTO;
    renewal_day_of_month: number | null;
    renewable_amount: number | null;
    created: number;
    updated: number;
    expires: number | null;
}

export interface NewCreditAccountDTO {
    name: string;
    init_amount?: number;
    renewable_amount?: number;
    renewal_day_of_month?: number;
    expires?: number;
}

export interface CreditAccountsResponseDTO extends ResponseTotalsDTO {
    credit_accounts: CreditAccountDTO[];
}
