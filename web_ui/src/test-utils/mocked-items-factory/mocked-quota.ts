// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Quota, QUOTA_TYPE } from '../../core/credits/subscriptions/quotas.interface';

export const getMockedQuota = (quota: Partial<Quota> = {}): Quota => ({
    id: '123',
    organizationId: 'organization-id',
    serviceName: 'service-name',
    quotaName: 'quota-name',
    quotaType: QUOTA_TYPE.MAX_TRAINING_JOBS,
    limit: 1,
    created: Date.now(),
    updated: Date.now(),
    maxLimit: undefined,
    ...quota,
});
