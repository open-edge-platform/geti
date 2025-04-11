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
