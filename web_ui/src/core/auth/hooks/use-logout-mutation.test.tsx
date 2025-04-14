// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook } from '@testing-library/react';
import { rest } from 'msw';

import { server } from '../../annotations/services/test-utils';
import { ApplicationServicesProvider } from '../../services/application-services-provider.component';
import { apiRequestUrl } from '../../services/test-utils';
import { API_URLS } from '../../services/urls';
import { useLogoutMutation } from './use-logout-mutation.hook';

describe('useLogoutMutation', () => {
    const wrapper = ({ children }: { children?: ReactNode }) => {
        const queryClient = new QueryClient();

        return (
            <ApplicationServicesProvider useInMemoryEnvironment={false}>
                <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
            </ApplicationServicesProvider>
        );
    };

    it('calls the auth cookie endpoint with an authorization header', async () => {
        const setAuthHeader = jest.fn();

        server.use(
            rest.post(apiRequestUrl(`api/${API_URLS.LOGOUT}`), (_req, res, ctx) => {
                setAuthHeader();
                return res(ctx.status(200));
            })
        );

        const { result } = renderHook(() => useLogoutMutation(), { wrapper });

        await act(async () => {
            await result.current.mutateAsync();
        });

        expect(setAuthHeader).toHaveBeenCalled();
    });
});
