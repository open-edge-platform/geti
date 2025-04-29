// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { QuotaDTO, QuotasResponseDTO } from '../dtos/quotas.interface';
import { SubscriptionDTO } from '../dtos/subscription.interface';
import { Quota, QUOTA_TYPE, QuotasResponse } from '../quotas.interface';
import { Subscription, SubscriptionStatus } from '../subscription.interface';

export const getSubscriptionEntity = (subscription: SubscriptionDTO): Subscription => {
    const {
        id,
        organization_id,
        workspace_id,
        product_id,
        status,
        created,
        updated,
        next_renewal_date,
        previous_renewal_date,
    } = subscription;

    return {
        id,
        organizationId: organization_id,
        workspaceId: workspace_id,
        productId: product_id,
        status: status as SubscriptionStatus,
        created,
        updated,
        nextRenewalDate: next_renewal_date,
        previousRenewalDate: previous_renewal_date,
    };
};

const MAX_TRAINING_JOBS_LIMIT = 20;

export const getQuotaEntity = (quotaDTO: QuotaDTO): Quota => {
    const { id, organization_id, service_name, quota_name, quota_type, limit, created, updated } = quotaDTO;

    const maxLimit: number | undefined =
        quota_type === QUOTA_TYPE.MAX_TRAINING_JOBS ? MAX_TRAINING_JOBS_LIMIT : undefined;

    return {
        id,
        organizationId: organization_id,
        serviceName: service_name,
        quotaName: quota_name,
        quotaType: quota_type as QUOTA_TYPE,
        limit,
        created,
        updated,
        maxLimit,
    };
};

export const getQuotasResponseEntity = (responseDTO: QuotasResponseDTO): QuotasResponse => {
    const { quotas, total_matched, next_page } = responseDTO;

    return {
        quotas: quotas.map(getQuotaEntity),
        totalMatched: total_matched,
        nextPage: next_page,
    };
};

export const getQuotaDTO = (quota: Quota): QuotaDTO => {
    const { id, organizationId, serviceName, quotaName, quotaType, limit, created, updated } = quota;

    return {
        id,
        organization_id: organizationId,
        service_name: serviceName,
        quota_name: quotaName,
        quota_type: quotaType,
        limit,
        created,
        updated,
    };
};
