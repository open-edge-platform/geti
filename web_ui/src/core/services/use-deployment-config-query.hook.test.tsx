// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { waitFor } from '@testing-library/react';
import { rest } from 'msw';

import { renderHookWithProviders } from '../../test-utils/render-hook-with-providers';
import { server } from '../annotations/services/test-utils';
import { DeploymentConfiguration, useDeploymentConfigQuery } from './use-deployment-config-query.hook';
import { isAdminLocation } from './utils';

// Note: On setupTests we're globally mocking this hook, so to test it here we need to override to the default (initial) value
jest.mock('./use-deployment-config-query.hook', () => jest.requireActual('./use-deployment-config-query.hook'));
jest.mock('./utils', () => ({
    ...jest.requireActual('./utils'),
    isAdminLocation: jest.fn(() => false),
}));

describe('useDeploymentConfigQuery', () => {
    afterEach(() => {
        jest.restoreAllMocks();
    });

    const saasDeploymentData: DeploymentConfiguration = {
        servingMode: 'saas',
        auth: {
            authority: 'https://app.geti.intel.com/',
            clientId: 'custom-geti-client-id',
            type: 'cidaas',
        },
        controlPlaneUrl: null,
        dataPlaneUrl: null,
        configUrl: null,
        docsUrl: '/docs',
    } as const;

    const renderDeploymentConfigHook = ({ isAdmin = false }: { isAdmin?: boolean } = {}) => {
        jest.mocked(isAdminLocation).mockImplementation(() => isAdmin);

        return renderHookWithProviders(useDeploymentConfigQuery);
    };

    describe('not having a deployment config', () => {
        beforeEach(() => {
            server.use(
                rest.get('/deployment-config.json', (_, res, ctx) => {
                    return res(ctx.status(404));
                })
            );
            server.use(
                rest.get('/intel-admin/deployment-config.json', (_, res, ctx) => {
                    return res(ctx.status(404));
                })
            );
        });

        it('returns authorization config for dex', async () => {
            const { result } = renderDeploymentConfigHook();

            await waitFor(() => {
                expect(result.current).not.toBeUndefined();
            });

            const data = result.current.data;
            expect(data?.servingMode).toEqual('on-prem');
            expect(data?.auth.type).toEqual('dex');
            expect(data?.auth.clientId).toEqual('web_ui');
            expect(data?.auth.authority).toEqual('/dex');
            expect(data?.controlPlaneUrl).toEqual(null);
            expect(data?.dataPlaneUrl).toEqual(null);
        });

        it('returns authorization config for intel sso', async () => {
            const { result } = renderDeploymentConfigHook({ isAdmin: true });

            await waitFor(() => {
                expect(result.current).not.toBeUndefined();
            });

            const data = result.current.data;
            expect(data?.servingMode).toEqual('saas');
            expect(data?.auth.type).toEqual('admin');
            expect(data?.auth.clientId).toEqual('214c9cd7-282c-446b-8d2f-34d7a93fece2');
            expect(data?.auth.authority).toEqual(
                'https://login.microsoftonline.com/46c98d88-e344-4ed4-8496-4ed7712e255d/v2.0'
            );
            expect(data?.controlPlaneUrl).toEqual(null);
            expect(data?.dataPlaneUrl).toEqual(null);
        });
    });

    it('returns authorization config from deployment information', async () => {
        server.use(
            rest.get('/deployment-config.json', (_, res, ctx) => {
                return res(ctx.json(saasDeploymentData));
            })
        );

        const { result } = renderDeploymentConfigHook();

        await waitFor(() => {
            expect(result.current).not.toBeUndefined();
        });

        const data = result.current.data;
        expect(data?.servingMode).toEqual('saas');
        expect(data?.auth.type).toEqual('cidaas');
        expect(data?.auth.clientId).toEqual('custom-geti-client-id');
        expect(data?.auth.authority).toEqual('https://app.geti.intel.com/');
        expect(data?.controlPlaneUrl).toEqual(null);
        expect(data?.dataPlaneUrl).toEqual(null);
    });

    it('returns authorization config from admin deployment information', async () => {
        server.use(
            rest.get('/intel-admin/deployment-config.json', (_, res, ctx) => {
                const deploymentConfiguration: DeploymentConfiguration = {
                    servingMode: 'saas',
                    auth: {
                        authority: 'https://app.geti.intel.com/',
                        clientId: 'custom-geti-client-id',
                        type: 'admin',
                    },
                    controlPlaneUrl: null,
                    dataPlaneUrl: null,
                    configUrl: null,
                    docsUrl: '/docs',
                };
                return res(ctx.json(deploymentConfiguration));
            })
        );

        const { result } = renderDeploymentConfigHook({ isAdmin: true });

        await waitFor(() => {
            expect(result.current).not.toBeUndefined();
        });

        const data = result.current.data;
        expect(data?.servingMode).toEqual('saas');
        expect(data?.auth.type).toEqual('admin');
        expect(data?.auth.clientId).toEqual('custom-geti-client-id');
        expect(data?.auth.authority).toEqual('https://app.geti.intel.com/');
        expect(data?.controlPlaneUrl).toEqual(null);
        expect(data?.dataPlaneUrl).toEqual(null);
        expect(data?.configUrl).toEqual(null);
    });

    it('allows using a path for dex authority', async () => {
        server.use(
            rest.get('/intel-admin/deployment-config.json', (_, res, ctx) => {
                const deploymentConfiguration: DeploymentConfiguration = {
                    servingMode: 'saas',
                    auth: {
                        authority: '/dex',
                        clientId: 'custom-geti-client-id',
                        type: 'admin',
                    },
                    controlPlaneUrl: null,
                    dataPlaneUrl: null,
                    configUrl: null,
                    docsUrl: '/docs',
                };
                return res(ctx.json(deploymentConfiguration));
            })
        );

        const { result } = renderDeploymentConfigHook({ isAdmin: true });

        await waitFor(() => {
            expect(result.current).not.toBeUndefined();
        });

        const data = result.current.data;
        expect(data?.servingMode).toEqual('saas');
        expect(data?.auth.type).toEqual('admin');
        expect(data?.auth.clientId).toEqual('custom-geti-client-id');
        expect(data?.auth.authority).toEqual('/dex');
        expect(data?.controlPlaneUrl).toEqual(null);
        expect(data?.dataPlaneUrl).toEqual(null);
        expect(data?.configUrl).toEqual(null);
    });

    it('returns the default config if deployment information is incorrect', async () => {
        server.use(
            rest.get('/intel-admin/deployment-config.json', (_, res, ctx) => {
                const deploymentConfiguration: DeploymentConfiguration = {
                    // @ts-expect-error This tests a faulty deployment configuration
                    servingMode: 'test',
                    // @ts-expect-error This tests a faulty deployment configuration
                    auth: null,
                    controlPlaneUrl: '',
                    dataPlaneUrl: '',
                    docsUrl: '/docs',
                };

                return res(ctx.json(deploymentConfiguration));
            })
        );

        const { result } = renderDeploymentConfigHook({ isAdmin: true });

        await waitFor(() => {
            expect(result.current).not.toBeUndefined();
        });

        const data = result.current.data;
        expect(data?.servingMode).toEqual('saas');
        expect(data?.auth.type).toEqual('admin');
        expect(data?.auth.clientId).toEqual('214c9cd7-282c-446b-8d2f-34d7a93fece2');
        expect(data?.auth.authority).toEqual(
            'https://login.microsoftonline.com/46c98d88-e344-4ed4-8496-4ed7712e255d/v2.0'
        );
        expect(data?.controlPlaneUrl).toEqual(null);
        expect(data?.dataPlaneUrl).toEqual(null);
        expect(data?.configUrl).toEqual(null);
    });

    it('returns a default docsUrl if it was omitted', async () => {
        server.use(
            rest.get('/intel-admin/deployment-config.json', (_, res, ctx) => {
                // @ts-expect-error This tests a faulty deployment configuration
                const deploymentConfiguration: DeploymentConfiguration = {
                    servingMode: 'saas',
                    auth: {
                        authority: 'https://app.geti.intel.com/',
                        clientId: 'custom-geti-client-id',
                        type: 'admin',
                    },
                    controlPlaneUrl: null,
                    dataPlaneUrl: null,
                    configUrl: null,
                };
                return res(ctx.json(deploymentConfiguration));
            })
        );

        const { result } = renderDeploymentConfigHook({ isAdmin: true });

        await waitFor(() => {
            expect(result.current).not.toBeUndefined();
        });

        const data = result.current.data;
        expect(data?.docsUrl).toEqual('https://docs.geti.intel.com/cloud/');
    });

    it('ignores the data and control plane urls', async () => {
        server.use(
            rest.get('/deployment-config.json', (_, res, ctx) => {
                const deploymentConfiguration: DeploymentConfiguration = {
                    ...saasDeploymentData,
                    controlPlaneUrl: 'https://api.geti.intel.com',
                    dataPlaneUrl: 'https://api.geti.intel.com',
                };

                return res(ctx.json(deploymentConfiguration));
            })
        );

        const { result } = renderDeploymentConfigHook();

        await waitFor(() => {
            expect(result.current).not.toBeUndefined();
        });

        const data = result.current.data;
        expect(data?.controlPlaneUrl).toBeNull();
        expect(data?.dataPlaneUrl).toBeNull();
    });

    describe('trailing slash on docsUrl', () => {
        it('adds a missing trailing slash to docs url', async () => {
            server.use(
                rest.get('/deployment-config.json', (_, res, ctx) => {
                    const deploymentConfiguration: DeploymentConfiguration = {
                        ...saasDeploymentData,
                        docsUrl: 'https://public-docs.geti.example.com/1.13',
                    };

                    return res(ctx.json(deploymentConfiguration));
                })
            );

            const { result } = renderDeploymentConfigHook();

            await waitFor(() => {
                expect(result.current).not.toBeUndefined();
            });

            const data = result.current.data;
            expect(data?.docsUrl).toEqual('https://public-docs.geti.example.com/1.13/');
        });

        it('does not add a double trailing slash to docs url', async () => {
            server.use(
                rest.get('/deployment-config.json', (_, res, ctx) => {
                    const deploymentConfiguration: DeploymentConfiguration = {
                        ...saasDeploymentData,
                        docsUrl: 'https://public-docs.geti.example.com/1.13/',
                    };

                    return res(ctx.json(deploymentConfiguration));
                })
            );

            const { result } = renderDeploymentConfigHook();

            await waitFor(() => {
                expect(result.current).not.toBeUndefined();
            });

            const data = result.current.data;
            expect(data?.docsUrl).toEqual('https://public-docs.geti.example.com/1.13/');
        });
    });
});
