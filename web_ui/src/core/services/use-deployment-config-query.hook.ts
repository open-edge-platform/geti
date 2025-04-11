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

import { useSuspenseQuery, UseSuspenseQueryOptions } from '@tanstack/react-query';
import axios from 'axios';
import { object, string } from 'yup';

import { oidcConfigCidaas, oidcConfigIntelSSO } from './../../core/auth/configuration';
import { isAdminLocation } from './utils';

export interface DeploymentConfiguration {
    servingMode: 'on-prem' | 'saas';
    auth: {
        type: 'dex' | 'cidaas' | 'admin';
        clientId: string;
        authority: string;
    };
    docsUrl: string;
    dataPlaneUrl: string | null;
    controlPlaneUrl: string | null;
    configUrl: string | null;
}

const deploymentConfigurationBasedOnFeatureFlags = (isAdmin: boolean): DeploymentConfiguration => {
    const servingMode: 'saas' | 'on-prem' = isAdmin ? 'saas' : 'on-prem';

    if (servingMode === 'on-prem') {
        return {
            servingMode,
            auth: {
                type: 'dex',
                clientId: 'web_ui',
                authority: '/dex',
            },
            controlPlaneUrl: null,
            dataPlaneUrl: null,
            docsUrl: 'https://docs.geti.intel.com/on-prem/2.6/',
            configUrl: null,
        };
    }

    const clientId = isAdmin
        ? oidcConfigIntelSSO(window.origin, window.localStorage).client_id
        : oidcConfigCidaas(window.origin, window.localStorage).client_id;
    const authority = isAdmin
        ? oidcConfigIntelSSO(window.origin, window.localStorage).authority
        : oidcConfigCidaas(window.origin, window.localStorage).authority;

    if (clientId === undefined || authority === undefined) {
        throw new Error('No client_id or authority set in deployment configuration.');
    }

    return {
        servingMode,
        auth: {
            type: isAdmin ? 'admin' : 'cidaas',
            clientId,
            authority,
        },
        controlPlaneUrl: null,
        dataPlaneUrl: null,
        docsUrl: 'https://docs.geti.intel.com/cloud/',
        configUrl: null,
    };
};

export const deploymentConfigQueryOptions = (isAdmin: boolean): UseSuspenseQueryOptions<DeploymentConfiguration> => {
    return {
        queryKey: ['deployment-config', isAdmin],
        queryFn: async (): Promise<DeploymentConfiguration> => {
            try {
                const url = isAdmin ? '/intel-admin/deployment-config.json' : '/deployment-config.json';

                const deployment = await axios.get<DeploymentConfiguration>(url);

                const deploymentSchema = object<DeploymentConfiguration>({
                    servingMode: string().oneOf(['saas', 'on-prem']).required(),
                    auth: object({
                        type: string().oneOf(['dex', 'cidaas', 'admin']).required(),
                        clientId: string().required(),
                        authority: string().required(),
                    }),
                    controlPlaneUrl: string().url().nullable(),
                    dataPlaneUrl: string().url().nullable(),
                    docsUrl: string().nullable(),
                    configUrl: string().nullable(),
                });

                await deploymentSchema.validate(deployment.data);

                let docsUrl = deployment.data.docsUrl ?? 'https://docs.geti.intel.com/cloud/';

                if (!docsUrl.endsWith('/')) {
                    docsUrl += '/';
                }

                // The cloud environments currently set a data and control
                // plane in the deployment configuration, but don't support
                // CORS so we disable this until they do
                if (process.env.REACT_APP_BUILD_TARGET !== 'admin_standalone') {
                    deployment.data.controlPlaneUrl = null;
                    deployment.data.dataPlaneUrl = null;
                }

                return {
                    ...deployment.data,
                    docsUrl,
                };
            } catch (error) {
                console.error(error);
                return deploymentConfigurationBasedOnFeatureFlags(isAdmin);
            }
        },
        staleTime: Infinity,
        gcTime: Infinity,
    };
};

export const useDeploymentConfigQuery = () => {
    const isAdmin = isAdminLocation();

    return useSuspenseQuery(deploymentConfigQueryOptions(isAdmin));
};
