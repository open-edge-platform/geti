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

import { renderHook } from '@testing-library/react';

import { useDeploymentConfigQuery } from '../services/use-deployment-config-query.hook';
import { useOIDCConfiguration } from './use-oidc-configuration.hook';

jest.mock('../services/use-deployment-config-query.hook', () => ({
    useDeploymentConfigQuery: jest.fn(),
}));

describe('useOIDCConfiguration', () => {
    it('returns authorization config for dex', () => {
        const data = {
            servingMode: 'on-prem',
            auth: {
                type: 'dex',
                authority: '/dex',
                clientId: 'web_ui',
            },
            dataPlaneUrl: null,
            controlPlaneUrl: null,
        } as const;

        // @ts-expect-error We only use data
        jest.mocked(useDeploymentConfigQuery).mockReturnValue({ data });

        const { result } = renderHook(() => useOIDCConfiguration(false));

        const configuration = result.current;

        expect(configuration.authority).toEqual('/dex');
        expect(configuration.client_id).toEqual('web_ui');

        expect(configuration.redirect_uri).toEqual('/callback');

        expect(configuration.scope).toEqual('openid profile groups email offline_access');
        expect(configuration.response_type).toEqual('code');
        expect(configuration.metadata).toEqual({
            authorization_endpoint: 'http://localhost/dex/auth/regular_users',
            token_endpoint: 'http://localhost/dex/token',
            end_session_endpoint: 'http://localhost',
        });
    });

    it('returns authorization config for cidaas', () => {
        const data = {
            servingMode: 'saas',
            auth: {
                type: 'cidaas',
                authority: 'https://consumer.example.com/oidc',
                clientId: 'some-client-id',
            },
            dataPlaneUrl: 'https://geti-cidaasfinal.geti.example.com/',
            controlPlaneUrl: 'https://geti-cidaasfinal.geti.example.com/',
        } as const;

        // @ts-expect-error We only use data
        jest.mocked(useDeploymentConfigQuery).mockReturnValue({ data });

        const { result } = renderHook(() => useOIDCConfiguration(false));

        const configuration = result.current;

        expect(configuration.authority).toEqual(data.auth.authority);
        expect(configuration.client_id).toEqual(data.auth.clientId);
        expect(configuration.scope).toEqual(data.auth.clientId);

        expect(configuration.redirect_uri).toEqual('http://localhost/callback');
        expect(configuration.post_logout_redirect_uri).toEqual('http://localhost/logout');

        expect(configuration.response_type).toEqual('code');
        expect(configuration.metadata).toEqual(undefined);
    });

    it('returns production authorization config for cidaas', () => {
        const data = {
            servingMode: 'saas',
            auth: {
                type: 'cidaas',
                authority: 'https://consumer.example.com/oidc',
                clientId: 'some-client-id',
            },
            dataPlaneUrl: 'https://geti-cidaasfinal.geti.example.com/',
            controlPlaneUrl: 'https://geti-cidaasfinal.geti.example.com/',
        } as const;

        // @ts-expect-error We only use data
        jest.mocked(useDeploymentConfigQuery).mockReturnValue({ data });

        const { result } = renderHook(() => useOIDCConfiguration(false));

        const configuration = result.current;

        expect(configuration.authority).toEqual(data.auth.authority);
        expect(configuration.client_id).toEqual(data.auth.clientId);
        expect(configuration.scope).toEqual(data.auth.clientId);

        expect(configuration.redirect_uri).toEqual('http://localhost/callback');
        expect(configuration.post_logout_redirect_uri).toEqual('http://localhost/logout');

        expect(configuration.response_type).toEqual('code');
        expect(configuration.metadata).toEqual(undefined);
    });

    it('returns authorization config for admin', () => {
        const data = {
            servingMode: 'saas',
            auth: {
                type: 'admin',
                authority: 'https://geti.example.com/oidc',
                clientId: 'some-client-id',
            },
            dataPlaneUrl: 'https://geti-cidaasfinal.geti.example.com/',
            controlPlaneUrl: 'https://geti-cidaasfinal.geti.example.com/',
        } as const;

        // @ts-expect-error We only use data
        jest.mocked(useDeploymentConfigQuery).mockReturnValue({ data });

        const { result } = renderHook(() => useOIDCConfiguration(true));

        const configuration = result.current;

        expect(configuration.authority).toEqual(data.auth.authority);
        expect(configuration.client_id).toEqual(data.auth.clientId);
        expect(configuration.scope).toEqual('openid');

        expect(configuration.redirect_uri).toEqual('http://localhost/intel-admin/callback');
        expect(configuration.post_logout_redirect_uri).toEqual('http://localhost/intel-admin/logout');

        expect(configuration.response_type).toEqual('code');
        expect(configuration.metadata).toEqual(undefined);
    });

    it('returns intel sso config for admin auth type', () => {
        const data = {
            servingMode: 'saas',
            auth: {
                type: 'admin',
                authority: 'https://geti.example.com/oidc',
                clientId: 'some-client-id',
            },
            dataPlaneUrl: 'https://geti-cidaasfinal.geti.example.com/',
            controlPlaneUrl: 'https://geti-cidaasfinal.geti.example.com/',
        } as const;

        // @ts-expect-error We only use data
        jest.mocked(useDeploymentConfigQuery).mockReturnValue({ data });

        const { result } = renderHook(() => useOIDCConfiguration(false));

        const configuration = result.current;

        expect(configuration.authority).toEqual(data.auth.authority);
        expect(configuration.client_id).toEqual(data.auth.clientId);
        expect(configuration.scope).toEqual('openid');

        expect(configuration.redirect_uri).toEqual('http://localhost/intel-admin/callback');
        expect(configuration.post_logout_redirect_uri).toEqual('http://localhost/intel-admin/logout');

        expect(configuration.response_type).toEqual('code');
        expect(configuration.metadata).toEqual(undefined);
    });

    it('returns production authorization config for admin', () => {
        const data = {
            servingMode: 'saas',
            auth: {
                type: 'admin',
                authority: 'https://prod/v2.0',
                clientId: 'prod',
            },
            dataPlaneUrl: 'https://geti-cidaasfinal.geti.example.com/',
            controlPlaneUrl: 'https://geti-cidaasfinal.geti.example.com/',
        } as const;

        // @ts-expect-error We only use data
        jest.mocked(useDeploymentConfigQuery).mockReturnValue({ data });

        const { result } = renderHook(() => useOIDCConfiguration(true));

        const configuration = result.current;

        expect(configuration.authority).toEqual(data.auth.authority);
        expect(configuration.client_id).toEqual(data.auth.clientId);
        expect(configuration.scope).toEqual('openid');

        expect(configuration.redirect_uri).toEqual('http://localhost/intel-admin/callback');
        expect(configuration.post_logout_redirect_uri).toEqual('http://localhost/intel-admin/logout');

        expect(configuration.response_type).toEqual('code');
        expect(configuration.metadata).toEqual(undefined);
    });

    it('returns authorization config for dex when auth type is dex', () => {
        const data = {
            servingMode: 'saas',
            auth: {
                type: 'dex',
                authority: '/dex',
                clientId: 'web_ui',
            },
            dataPlaneUrl: null,
            controlPlaneUrl: null,
        } as const;

        // @ts-expect-error We only use data
        jest.mocked(useDeploymentConfigQuery).mockReturnValue({ data });

        const { result } = renderHook(() => useOIDCConfiguration(false));

        const configuration = result.current;

        expect(configuration.authority).toEqual('/dex');
        expect(configuration.client_id).toEqual('web_ui');
        expect(configuration.metadata).not.toEqual(undefined);
    });
});
