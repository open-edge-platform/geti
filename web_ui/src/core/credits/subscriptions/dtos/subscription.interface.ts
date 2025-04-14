// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export interface SubscriptionDTO {
    id: number;
    organization_id: string;
    workspace_id: string;
    product_id: number;
    status: string;
    created: number;
    updated: number;
    next_renewal_date: number;
    previous_renewal_date: number | null;
}
