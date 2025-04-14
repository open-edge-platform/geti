// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
