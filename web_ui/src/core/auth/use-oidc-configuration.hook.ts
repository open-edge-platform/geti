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

import { AuthProviderProps } from 'react-oidc-context';

import { useDeploymentConfigQuery } from '../../core/services/use-deployment-config-query.hook';
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
