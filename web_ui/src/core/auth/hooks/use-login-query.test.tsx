// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, Suspense } from 'react';

import { ApplicationServicesProvider } from '@geti/core/src/services/application-services-provider.component';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { AuthContextProps } from 'react-oidc-context';

import { server } from '../../annotations/services/test-utils';
import { apiRequestUrl } from '../../services/test-utils';
import { API_URLS } from '../../services/urls';
import { useLoginQuery } from './use-login-query.hook';

describe('useLoginQuery', () => {
    const wrapper = ({ children }: { children?: ReactNode }) => {
        const queryClient = new QueryClient();

        return (
            <Suspense fallback={'loading...'}>
                <ApplicationServicesProvider useInMemoryEnvironment={false}>
                    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
                </ApplicationServicesProvider>
            </Suspense>
        );
    };

    it('calls the auth cookie endpoint with an authorization header', async () => {
        const setAuthHeader = jest.fn();

        server.use(
            rest.post(apiRequestUrl(`api/${API_URLS.AUTH_COOKIE}`), (req, res, ctx) => {
                setAuthHeader(req.headers.get('Authorization'));
                return res(ctx.status(200));
            })
        );

        const auth = {
            user: {
                id_token: 'test-token',
            },
        } as unknown as AuthContextProps;
        const { result } = renderHook(() => useLoginQuery(auth), { wrapper });

        await waitFor(() => {
            return result.current.isPending === false;
        });

        expect(setAuthHeader).toHaveBeenCalledWith('Bearer test-token');
    });
});
