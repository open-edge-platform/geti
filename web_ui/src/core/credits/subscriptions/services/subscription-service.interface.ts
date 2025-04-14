// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { OrganizationIdentifier } from '../../../organizations/organizations.interface';
import { Quota, QuotasResponse } from '../quotas.interface';
import { Subscription } from '../subscription.interface';

export interface GetQuotasQueryOptions {
    skip?: number;
    limit?: number;
}

export interface SubscriptionsService {
    getActiveSubscription: (id: OrganizationIdentifier) => Promise<Subscription>;
    getQuotas: (id: OrganizationIdentifier, options?: GetQuotasQueryOptions) => Promise<QuotasResponse>;
    updateQuota: (quota: Quota) => Promise<void>;
}
