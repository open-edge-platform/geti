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
