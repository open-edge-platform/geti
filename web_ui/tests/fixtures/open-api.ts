// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { test as baseTest, mergeTests } from '@playwright/test';
import { ResponseComposition, RestContext } from 'msw';
import { User } from 'oidc-client-ts';
import OpenAPIBackend from 'openapi-backend';

import {
    CustomFeatureFlags,
    DEV_FEATURE_FLAGS,
} from '../../src/core/feature-flags/services/feature-flag-service.interface';
import { OpenApiRequest, OpenApiResponse, OperationId } from '../../src/core/server/types';
import { handleRoute } from './open-api/handle-route';
import { notFoundHandler, setupOpenApiHandler } from './open-api/setup-open-api-handlers';

export interface ImportFile {
    name: string;
    size: number;
    buffer?: Buffer;
}

export type ApiResponse = (
    req: OpenApiRequest<OperationId>,
    res: ResponseComposition<OpenApiResponse<OperationId>['body']>,
    ctx: RestContext
) => OpenApiResponse<OperationId> | Promise<OpenApiResponse<OperationId>>;

export interface OpenApiFixtures {
    openApi: OpenAPIBackend;
    setupOpenAPIServer: void;

    registerApiExample: (operationId: OperationId, example: string, code?: number) => void;

    registerApiResponse: <OpId extends OperationId>(
        operationId: OpId,
        response: (
            req: OpenApiRequest<OpId>,
            // @ts-expect-error ignore
            res: ResponseComposition<OpenApiResponse<OpId>['body']>,
            ctx: RestContext
        ) => OpenApiResponse<OpId> | Promise<OpenApiResponse<OpId>>
    ) => void;

    featureFlags: CustomFeatureFlags;
    isSaaS: boolean;
    registerFeatureFlags: (featureFlags: CustomFeatureFlags) => void;
}

export const testWithLocalStorageState = <Test extends typeof baseTest>(
    test: Test,
    getLocalStorage: () => Promise<Array<{ name: string; value: string }>>
) => {
    return mergeTests(
        test,
        baseTest.extend<{ initialOidcUser: undefined | User }>({
            /**
             * Setup a default localstorage setting for our component tests where
             * our oidc library is configured to be logged in as an admin user
             **/
            storageState: async ({ baseURL }, use) => {
                if (baseURL === undefined) {
                    return use({ cookies: [], origins: [] });
                }

                return use({
                    cookies: [],
                    origins: [{ origin: baseURL, localStorage: await getLocalStorage() }],
                });
            },

            initialOidcUser: async ({ storageState, baseURL }, use) => {
                if (storageState === undefined || typeof storageState === 'string') {
                    return use(undefined);
                }

                // Find the storage state strign associated to the current baseURL
                const origin = storageState.origins.find((state) => state.origin === baseURL);
                const oidcStorageString = origin?.localStorage.find((state) => state.name.includes('oidc.user'))?.value;

                if (oidcStorageString === undefined) {
                    return use(undefined);
                }

                // Assume the storage state string is an oidc user
                return use(User.fromStorageString(oidcStorageString));
            },
        })
    );
};

const registerFeatureFlags = (openApi: OpenAPIBackend) => {
    return (featureFlags: CustomFeatureFlags) => {
        openApi.registerHandler('list_feature_flags_feature_flags__get', (c, res, ctx) => {
            if (c.request.path === '/feature_flags') {
                return res(ctx.status(200), ctx.json({ ...DEV_FEATURE_FLAGS, ...featureFlags }));
            }

            return notFoundHandler(c, res, ctx);
        });
    };
};

export function extendWithOpenApi<Test extends typeof baseTest>(test: Test) {
    // Set expiration time of our current session as 1 hour in the future
    const expirationTime = (Date.now() + 60 * 60 * 1000) / 1000;
    const oidc = JSON.stringify({
        id_token: '<redacted>',
        session_state: null,
        access_token: '<redacted>',
        refresh_token: '<redacted>',
        token_type: 'bearer',
        scope: 'openid profile groups email offline_access',
        profile: {
            iss: '<redacted>',
            sub: '<redacted>',
            aud: 'web_ui',
            exp: expirationTime,
            iat: expirationTime,
            c_hash: '<redacted>',
            email: 'admin@intel.com',
            email_verified: true,
            name: 'Admin',
            preferred_username: 'Admin',
        },
        expires_at: expirationTime,
    });

    const localStorage = [{ name: 'oidc.user:/dex:web_ui', value: oidc }];

    return mergeTests(
        test,
        testWithLocalStorageState(baseTest, async () => localStorage).extend<OpenApiFixtures>({
            featureFlags: [DEV_FEATURE_FLAGS, { option: true }],
            isSaaS: false,
            openApi: async ({}, use) => {
                const openApi = await setupOpenApiHandler();

                await use(openApi);
            },
            setupOpenAPIServer: [
                async ({ page, openApi, isSaaS, baseURL }, use) => {
                    const servers = openApi.definition.servers ?? [];

                    for await (const server of servers) {
                        const url = server.url;

                        await page.route(`${url}/**/*`, async (route) => {
                            try {
                                const handled = await handleRoute(route, openApi, url);

                                if (!handled) {
                                    await route.continue();
                                }
                            } catch (error: unknown) {
                                await route.fulfill({
                                    status: 502,
                                    body: (error as Error).message,
                                });
                            }
                        });
                    }

                    // Handle the deployment config file which is outside of our OpenAPI spec
                    // This file is used by the UI to determine our oidc (authentication)
                    // settings as well as the urls to use for accessing the REST api
                    const deploymentConfig = {
                        servingMode: isSaaS ? 'saas' : 'on-prem',
                        auth: {
                            type: 'dex',
                            authority: '/dex',
                            clientId: 'web_ui',
                        },
                        docsUrl: '/docs',
                        dataPlaneUrl: null,
                        controlPlaneUrl: null,
                        configUrl: isSaaS ? `${baseURL}/config.geti.example.com` : null,
                    };
                    await page.route('/deployment-config.json', async (route) => {
                        await route.fulfill({ status: 200, body: JSON.stringify(deploymentConfig) });
                    });
                    await page.route('/intel-admin/deployment-config.json', async (route) => {
                        await route.fulfill({ status: 200, body: JSON.stringify(deploymentConfig) });
                    });

                    await use();
                },
                {
                    /**
                     * Scope this fixture on per test basis to ensure that each test has a
                     * fresh copy of MSW. Note: the scope MUST be "test" to be able to use the
                     * `page` fixture as it is not possible to access it when scoped to the
                     * "worker".
                     */
                    scope: 'test',
                    /**
                     * By default, fixtures are lazy; they will not be initialised unless they're
                     * used by the test. Setting `true` here means that the fixture will be auto-
                     * initialised even if the test doesn't use it.
                     */
                    auto: true,
                },
            ],
            // use the registerApiExample fixture to mock an operation id using an example from
            // the backend's Open Api schema
            registerApiExample: async ({ openApi }, use) => {
                const registerApiExample = (operationId: string, example: string, code?: number) => {
                    openApi.registerHandler(operationId, (c, res, ctx) => {
                        const { status, mock } = c.api.mockResponseForOperation(operationId, { example, code });

                        return res(ctx.status(status), ctx.json(mock));
                    });
                };

                await use(registerApiExample);
            },

            registerApiResponse: async ({ openApi }, use) => {
                const registerApiResponse: OpenApiFixtures['registerApiResponse'] = (operationId, response) => {
                    openApi.registerHandler(operationId, (c, res, ctx) => {
                        // @ts-expect-error TODO: ideally we should validate the request
                        return response(c.request, res, ctx);
                    });
                };

                await use(registerApiResponse);
            },

            registerFeatureFlags: async ({ openApi }, use) => {
                await use(registerFeatureFlags(openApi));
            },
            // Decorate the page fixture so that each test is called with the default dev feature flags
            // NOTE: using the `registerFeatureFlags` fixture results in a cyclic dependency
            // so instead we call registerFeatureFlags twice
            page: async ({ page, openApi, featureFlags }, use) => {
                registerFeatureFlags(openApi)({ ...DEV_FEATURE_FLAGS, ...featureFlags });

                await use(page);
            },
        })
    );
}
