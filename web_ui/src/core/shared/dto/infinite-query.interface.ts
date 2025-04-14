// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
export interface InfiniteQueryDTO {
    totalCount: number;
    nextPage: {
        skip: number;
        limit: number;
    };
}
