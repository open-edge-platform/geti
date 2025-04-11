// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ReactNode, Suspense } from 'react';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { rest } from 'msw';

import { server } from '../../annotations/services/test-utils';
import { ApplicationServicesProvider } from '../../services/application-services-provider.component';
import { apiRequestUrl } from '../../services/test-utils';
import { API_URLS } from '../../services/urls';
import { useFeatureFlagQuery } from './use-feature-flag-query.hook';

describe('useFeatureFlagQuery', () => {
    const wrapper = ({ children }: { children?: ReactNode }) => {
        const queryClient = new QueryClient();

        return (
            <Suspense fallback='loading...'>
                <ApplicationServicesProvider useInMemoryEnvironment={false}>
                    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
                </ApplicationServicesProvider>
            </Suspense>
        );
    };

    it('returns the correct response', async () => {
        server.use(
            rest.get(apiRequestUrl(`api/${API_URLS.FEATURE_FLAGS}`), (_req, res, ctx) =>
                res(ctx.json({ FEATURE_FLAG_TEST_FEATURE_1: true, FEATURE_FLAG_TEST_FEATURE_2: false }))
            )
        );

        const { result } = renderHook(() => useFeatureFlagQuery(), { wrapper });

        await waitFor(() => {
            return result.current.isPending === false;
        });

        expect(result.current.data).toEqual({
            FEATURE_FLAG_TEST_FEATURE_1: true,
            FEATURE_FLAG_TEST_FEATURE_2: false,
        });
    });
});
