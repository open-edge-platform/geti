// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
