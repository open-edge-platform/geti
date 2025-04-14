// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { SortDirection } from '../../shared/components/table/table.interface';

export interface QueryParameters<T> {
    skip?: number;
    limit?: number;
    createdAtFrom?: string;
    createdAtTo?: string;
    modifiedAtFrom?: string;
    modifiedAtTo?: string;
    sortDirection?: SortDirection;
    sortBy?: T;
}
