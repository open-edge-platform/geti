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
