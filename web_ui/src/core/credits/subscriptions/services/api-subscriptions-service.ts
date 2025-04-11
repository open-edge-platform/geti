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
import { SubscriptionDTO } from '../dtos/subscription.interface';
import { SubscriptionsService } from './subscription-service.interface';
import { getQuotaDTO, getQuotasResponseEntity, getSubscriptionEntity } from './utils';

export const createApiSubscriptionsService: CreateApiService<SubscriptionsService> = (
    { instance: platformInstance, router } = { instance: defaultAxiosInstance, router: API_URLS }
) => {
    const getActiveSubscription: SubscriptionsService['getActiveSubscription'] = async ({ organizationId }) => {
        const { data } = await platformInstance.get<SubscriptionDTO>(router.ACTIVE_SUBSCRIPTION(organizationId));

        return getSubscriptionEntity(data);
    };

    const getQuotas: SubscriptionsService['getQuotas'] = async ({ organizationId }, options) => {
        try {
            const { data } = await platformInstance.get(router.ORGANIZATION_QUOTAS(organizationId), {
                params: options,
            });

            return getQuotasResponseEntity(data);
        } catch (_error) {
            return {
                quotas: [],
                totalMatched: 0,
                nextPage: null,
            };
        }
    };

    const updateQuota: SubscriptionsService['updateQuota'] = async (quota) => {
        await platformInstance.put(router.ORGANIZATION_QUOTAS(quota.organizationId), getQuotaDTO(quota));
    };

    return {
        getActiveSubscription,
        getQuotas,
        updateQuota,
    };
};
