// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
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
import { AuthContextProps } from 'react-oidc-context';

import { server } from '../../annotations/services/test-utils';
import { ApplicationServicesProvider } from '../../services/application-services-provider.component';
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
