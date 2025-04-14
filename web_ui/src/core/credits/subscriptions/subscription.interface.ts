// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export enum SubscriptionStatus {
    ACTIVE = 'active',
    CANCELLED = 'cancelled',
}

export interface Subscription {
    id: number;
    organizationId: string;
    workspaceId: string;
    productId: number;
    status: SubscriptionStatus;
    created: number;
    updated: number;
    nextRenewalDate: number;
    previousRenewalDate: number | null;
}
