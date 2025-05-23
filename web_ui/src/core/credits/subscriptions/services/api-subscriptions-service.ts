// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { apiClient } from '@geti/core';

import { CreateApiService } from '../../../../../packages/core/src/services/create-api-service.interface';
import { API_URLS } from '../../../../../packages/core/src/services/urls';
import { SubscriptionDTO } from '../dtos/subscription.interface';
import { SubscriptionsService } from './subscription-service.interface';
import { getQuotaDTO, getQuotasResponseEntity, getSubscriptionEntity } from './utils';

export const createApiSubscriptionsService: CreateApiService<SubscriptionsService> = (
    { instance: platformInstance, router } = { instance: apiClient, router: API_URLS }
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
