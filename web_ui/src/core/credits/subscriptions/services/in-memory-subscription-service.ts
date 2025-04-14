// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { QUOTA_TYPE } from '../quotas.interface';
import { SubscriptionStatus } from '../subscription.interface';
import { SubscriptionsService } from './subscription-service.interface';

export const createInMemorySubscriptionsService = (): SubscriptionsService => {
    const getActiveSubscription: SubscriptionsService['getActiveSubscription'] = () => {
        return Promise.resolve({
            id: 1,
            organizationId: '123',
            workspaceId: '123',
            productId: 1,
            status: SubscriptionStatus.ACTIVE,
            created: 1718794841877,
            updated: 1718794841877,
            nextRenewalDate: 1721347200000,
            previousRenewalDate: null,
        });
    };

    const getQuotas: SubscriptionsService['getQuotas'] = () => {
        return Promise.resolve({
            quotas: [
                {
                    id: '1',
                    organizationId: '123',
                    serviceName: 'training',
                    quotaName: 'Max number of concurrent training jobs',
                    quotaType: QUOTA_TYPE.MAX_TRAINING_JOBS,
                    limit: 10,
                    created: null,
                    updated: null,
                },
            ],
            totalMatched: 1,
            nextPage: null,
        });
    };

    const updateQuota: SubscriptionsService['updateQuota'] = () => {
        return Promise.resolve();
    };

    return {
        getActiveSubscription,
        getQuotas,
        updateQuota,
    };
};
