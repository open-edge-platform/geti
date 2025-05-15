// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
            docsUrl: 'https://docs.geti.intel.com/',
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
        docsUrl: 'https://docs.geti.intel.com/',
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

                let docsUrl = deployment.data.docsUrl ?? 'https://docs.geti.intel.com/';

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
