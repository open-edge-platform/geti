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
