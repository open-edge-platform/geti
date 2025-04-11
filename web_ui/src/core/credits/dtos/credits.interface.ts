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
