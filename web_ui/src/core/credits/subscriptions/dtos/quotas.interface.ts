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

export interface QuotaDTO {
    id: string;
    organization_id: string;
    service_name: string;
    quota_name: string;
    quota_type: string;
    limit: number;
    created: number | null;
    updated: number | null;
}

export interface QuotasResponseDTO {
    quotas: QuotaDTO[];
    total_matched: number;
    next_page: {
        skip: number;
        limit: number;
    } | null;
}
