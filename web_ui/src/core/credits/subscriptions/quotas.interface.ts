// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export enum QUOTA_TYPE {
    MAX_USERS_COUNT = 'MAX_USERS_COUNT',
    MAX_TRAINING_JOBS = 'MAX_TRAINING_JOBS',
}

export interface Quota {
    id: string;
    organizationId: string;
    serviceName: string;
    quotaName: string;
    quotaType: QUOTA_TYPE;
    limit: number;
    created: number | null;
    updated: number | null;
    maxLimit?: number;
}

export interface QuotasResponse {
    quotas: Quota[];
    totalMatched: number;
    nextPage: {
        skip: number;
        limit: number;
    } | null;
}
