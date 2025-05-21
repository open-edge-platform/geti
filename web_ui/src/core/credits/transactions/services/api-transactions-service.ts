// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { apiClient } from '@geti/core';

import { CreateApiService } from '../../../services/create-api-service.interface';
import { API_URLS } from '../../../services/urls';
import { TransactionsAggregatesDTO, TransactionsResponseDTO } from '../dtos/transactions.interface';
import { TransactionsService } from './transactions-service.interface';
import { getTransactionResponseEntity, getTransactionsAggregatesResponseEntity } from './utils';

export const createApiTransactionsService: CreateApiService<TransactionsService> = (
    { instance: platformInstance, router } = { instance: apiClient, router: API_URLS }
) => {
    const getTransactions: TransactionsService['getTransactions'] = async (orgId, options) => {
        const { data } = await platformInstance.get<TransactionsResponseDTO>(
            router.CREDIT_TRANSACTIONS(orgId, options)
        );

        return getTransactionResponseEntity(data);
    };

    const getTransactionsAggregates: TransactionsService['getTransactionsAggregates'] = async (orgId, options) => {
        const { data } = await platformInstance.get<TransactionsAggregatesDTO>(
            router.CREDIT_TRANSACTIONS_AGGREGATES(orgId, options)
        );

        return getTransactionsAggregatesResponseEntity(data);
    };

    return {
        getTransactions,
        getTransactionsAggregates,
    };
};
