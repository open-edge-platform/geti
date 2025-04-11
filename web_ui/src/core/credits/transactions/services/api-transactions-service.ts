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

import { instance as defaultAxiosInstance } from '../../../services/axios-instance';
import { CreateApiService } from '../../../services/create-api-service.interface';
import { API_URLS } from '../../../services/urls';
import { TransactionsAggregatesDTO, TransactionsResponseDTO } from '../dtos/transactions.interface';
import { TransactionsService } from './transactions-service.interface';
import { getTransactionResponseEntity, getTransactionsAggregatesResponseEntity } from './utils';

export const createApiTransactionsService: CreateApiService<TransactionsService> = (
    { instance: platformInstance, router } = { instance: defaultAxiosInstance, router: API_URLS }
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
