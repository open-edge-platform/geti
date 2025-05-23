// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { WebStorageStateStore } from 'oidc-client-ts';
import { AuthProviderProps } from 'react-oidc-context';

import { paths } from '../../../packages/core/src/services/routes';

/*
    # OpenID Connect (OIDC) and OAuth2 protocol support for browser-based JavaScript applications
    Package used: https://github.com/authts/react-oidc-context#documentation
    Based on: https://github.com/authts/oidc-client-ts

    ## Normal usage within React's context:

    ```
        import { useAuth } from "react-oidc-context";

        const { isLoading, error, isAuthenticated, etc... } = useAuth();
    ```

    ## If we need to access this information outside of React's context, we can:
    ```
        import { User } from "oidc-client-ts"

        const getUser = () =>  {
            const oidcStorage = localStorage.getItem(`oidc.user:<your authority>:<your client id>`)

            if (!oidcStorage) {
                return null;
            }

            return User.fromStorageString(oidcStorage);
        }
    ```
*/

export const oidcConfigDex = (origin: string, store: Storage): AuthProviderProps => {
    return {
        authority: `/dex`,
        client_id: 'web_ui',
        scope: 'openid profile groups email offline_access',
        metadata: {
            // We only need to override this field on the metadata, the rest should be the default.
            // All the metadata is gathered from <environment>/dex/.well-known/openid-configuration
            authorization_endpoint: `${origin}/dex/auth/regular_users`,
            token_endpoint: `${origin}/dex/token`,
            // Overwrite the end_session_endpoint as DEX does not support this, after
            // the user signs out this makes it so that we reload the main app and show
            // the login screen
            end_session_endpoint: origin,
        },
        response_type: 'code',
        userStore: new WebStorageStateStore({ store }),

        // Note: currently DEX only allows /callback as a redirect_uri, not including
        // localhost as a domain
        redirect_uri: `${paths.authProviderCallback.pattern}`,
    };
};

// This configuration should match the OIDC provider's configuration, in this case: CidaaS
export const oidcConfigCidaas = (origin: string, store: Storage): AuthProviderProps => {
    return {
        authority:
            'https://consumerdev.intel.com/intelcorpdevb2c.onmicrosoft.com/b2c_1a_unifiedlogin_sisu_cml_oidc/v2.0/',
        client_id: '0f3145e1-2415-4d6d-8af8-05c3111fe96e',
        scope: '0f3145e1-2415-4d6d-8af8-05c3111fe96e',
        response_type: 'code',
        userStore: new WebStorageStateStore({ store }),
        redirect_uri: origin + paths.authProviderCallback({}),
        post_logout_redirect_uri: origin + paths.logout({}),
    };
};

// https://login.microsoftonline.com/46c98d88-e344-4ed4-8496-4ed7712e255d/v2.0/.well-known/openid-configuration
export const oidcConfigIntelSSO = (origin: string, store: Storage): AuthProviderProps => {
    return {
        authority: 'https://login.microsoftonline.com/46c98d88-e344-4ed4-8496-4ed7712e255d/v2.0',
        client_id: '214c9cd7-282c-446b-8d2f-34d7a93fece2',
        scope: 'openid',
        response_type: 'code',
        userStore: new WebStorageStateStore({ store }),
        redirect_uri: origin + paths.intelAdmin.authProviderCallback({}),
        post_logout_redirect_uri: origin + paths.intelAdmin.logout({}),
    };
};
