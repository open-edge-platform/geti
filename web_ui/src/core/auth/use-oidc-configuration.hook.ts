// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useDeploymentConfigQuery } from '@geti/core/src/services/use-deployment-config-query.hook';
import { AuthProviderProps } from 'react-oidc-context';

import { oidcConfigCidaas, oidcConfigDex, oidcConfigIntelSSO } from './../../core/auth/configuration';

export const useOIDCConfiguration = (isAdmin: boolean): AuthProviderProps => {
    const deploymentConfig = useDeploymentConfigQuery();

    if (deploymentConfig.data === undefined) {
        throw new Error('Deployment config not yet loaded');
    }

    if (isAdmin || deploymentConfig.data.auth.type === 'admin') {
        return {
            ...oidcConfigIntelSSO(window.origin, window.localStorage),
            authority: deploymentConfig.data.auth.authority,
            client_id: deploymentConfig.data.auth.clientId,
        } as AuthProviderProps;
    }

    if (deploymentConfig.data.servingMode === 'on-prem' || deploymentConfig.data.auth.type === 'dex') {
        return oidcConfigDex(window.origin, window.localStorage);
    }

    return {
        ...oidcConfigCidaas(window.origin, window.localStorage),
        authority: deploymentConfig.data.auth.authority,
        client_id: deploymentConfig.data.auth.clientId,
        scope: deploymentConfig.data.auth.clientId,
    } as AuthProviderProps;
};
