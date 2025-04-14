// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { queryOptions } from '@tanstack/react-query';

/**
 * This function tries to mimicks tanstack/react-query v5's `queryOptions` API
 * However unlike v5 we require the user passing a generic which normally takes
 * either a `UseQueryOptions` type or an `UseInfiniteQueryOptions` type
 * The extra `RequiredFields` makes it so that we can use the output of
 * this function in queryClient.ensureQueryData
 *
 * This function intentionally does nothing, it merely provides extra type
 * information when writing and consuming query options
 *
 * @TODO Replace this once we migrate to @tanstack/react-query v5
 */
export { queryOptions };
