// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
