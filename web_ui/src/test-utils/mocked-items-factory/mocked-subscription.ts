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

import { Subscription, SubscriptionStatus } from '../../core/credits/subscriptions/subscription.interface';

export const getMockedSubscription = (subscription: Partial<Subscription> = {}): Subscription => ({
    id: 1,
    organizationId: '123',
    workspaceId: '345',
    productId: 1,
    status: SubscriptionStatus.ACTIVE,
    created: Date.now(),
    updated: Date.now(),
    nextRenewalDate: Date.now(),
    previousRenewalDate: null,
    ...subscription,
});
