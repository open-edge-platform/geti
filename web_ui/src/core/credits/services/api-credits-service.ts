// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { apiClient } from '@geti/core';

import { CreateApiService } from '../../../../packages/core/src/services/create-api-service.interface';
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
    { instance: platformInstance, router } = { instance: apiClient, router: API_URLS }
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
