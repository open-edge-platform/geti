// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export type NextPageURL = string | null | undefined;

export type NextPage = {
    skip: number;
    limit: number;
} | null;

export interface InfiniteQuery {
    totalCount: number;
    nextPage: NextPage;
}
