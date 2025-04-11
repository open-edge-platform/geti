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

import { instance as defaultAxiosInstance } from '../../services/axios-instance';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { CreditAccountDTO, CreditAccountsResponseDTO, OrganizationBalanceDTO } from '../dtos/credits.interface';
import { CreditsService } from './credits-service.interface';
import {
    getCreditAccountEntity,
    getCreditAccountsQueryOptionsDTO,
    getCreditAccountsResponseEntity,
    getNewCreditAccountEntityDTO,
} from './utils';

export const createApiCreditsService: CreateApiService<CreditsService> = (
    { instance: platformInstance, router } = { instance: defaultAxiosInstance, router: API_URLS }
) => {
    const getOrganizationBalance: CreditsService['getOrganizationBalance'] = async (organizationId) => {
        const { data } = await platformInstance.get<OrganizationBalanceDTO>(
            router.ORGANIZATION_BALANCE(organizationId)
        );

        return data;
    };

    const getCreditAccounts: CreditsService['getCreditAccounts'] = async (orgId, queryOptions) => {
        const { data } = await platformInstance.get<CreditAccountsResponseDTO>(router.CREDIT_ACCOUNTS(orgId), {
            params: getCreditAccountsQueryOptionsDTO(queryOptions),
        });

        return getCreditAccountsResponseEntity(data);
    };

    const getCreditAccount: CreditsService['getCreditAccount'] = async (id) => {
        const { data } = await platformInstance.get<CreditAccountDTO>(router.CREDIT_ACCOUNT(id));

        return getCreditAccountEntity(data);
    };

    const createCreditAccount: CreditsService['createCreditAccount'] = async (creditAccount) => {
        const payload = getNewCreditAccountEntityDTO(creditAccount);

        await platformInstance.post(router.CREDIT_ACCOUNTS(creditAccount), payload);
    };

    const updateCreditAccount: CreditsService['updateCreditAccount'] = async (id, creditAccount) => {
        const payload = getNewCreditAccountEntityDTO(creditAccount);

        const { data } = await platformInstance.put<CreditAccountDTO>(router.CREDIT_ACCOUNT(id), payload);

        return getCreditAccountEntity(data);
    };

    const updateCreditAccountBalance: CreditsService['updateCreditAccountBalance'] = async (id, balance) => {
        await platformInstance.put(router.CREDIT_ACCOUNT_BALANCE(id), balance);
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
