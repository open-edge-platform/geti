// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
export interface QueryParametersDTO<T> {
    skip?: number;
    limit?: number;
    createdAtFrom?: string;
    createdAtTo?: string;
    modifiedAtFrom?: string;
    modifiedAtTo?: string;
    sortDirection?: 'asc' | 'desc';
    sortBy?: T;
}
