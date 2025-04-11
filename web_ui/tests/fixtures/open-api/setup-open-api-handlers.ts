// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import * as fs from 'fs';
import * as path from 'path';

import isString from 'lodash/isString';
import { DefaultBodyType, ResponseComposition, RestContext } from 'msw';
import OpenAPIBackend, { type Context, type Document, type Options } from 'openapi-backend';

import definition from './../../../src/core/server/generated/api-spec.json';
import { settings, supportedAlgorithms } from './mocks';

const SHOW_UNIMPLEMENTED_OPERATIONS = false;

// The operation handler is called with msw's response composition and rest context handlers
// this is done via getMSWHandlers
interface OperationHandler {
    (c: Context<Document>, res: ResponseComposition<DefaultBodyType>, ctx: RestContext): unknown;
}

export const notFoundHandler: OperationHandler = (c, res, ctx) => {
    // The following responses are from the Gateway and License microservices,
    // which are not included in the OpenApi specification, so instead we will
    // provide manual mocks for these requests.
    // In the future we should add these endpoints to our internal OpenApi specification.
    switch (c.request.path) {
        case '/workspaces':
            return res(
                ctx.status(200),
                ctx.json({
                    workspaces: [
                        {
                            creation_date: '2021-07-28T09:07:13.999000+00:00',
                            creator_name: 'dummy',
                            description: 'This is the first workspace.',
                            id: '61011e42d891c82e13ec92da',
                            name: 'Workspace 1',
                        },
                        {
                            creation_date: '2021-07-28T09:07:15.985000+00:00',
                            creator_name: 'dummy',
                            description: 'This is another workspace.',
                            id: '61011e43d891c82e13ec952e',
                            name: 'Workspace 2',
                        },
                    ],
                })
            );
        case '/traces':
        case '/metrics': {
            return res(ctx.status(200), ctx.json({}));
        }
        /* TODO: remove this and use actual methods from the api spec once it's added by the platform team */
        case '/onboarding/user': {
            return res(ctx.status(200), ctx.json({}));
        }
        case '/users/active': {
            return res(
                ctx.status(200),
                ctx.json({
                    name: 'admin@intel.com',
                    uid: 'admin@intel.com',
                    mail: 'admin@intel.com',
                    roles: ['ADMIN'],
                    group: 500,
                    registered: true,
                    expiration_date: null,
                    email_token: null,
                })
            );
        }
        case '/users/admin@intel.com/roles': {
            return res(
                ctx.status(200),
                ctx.json({
                    roles: [
                        {
                            role: 'admin',
                            resource_type: 'workspace',
                            resource_id: '6316f068c868242d7f2072c4',
                        },
                    ],
                })
            );
        }
        case '/organizations': {
            return res(
                ctx.status(200),
                ctx.json({
                    organizations: [
                        {
                            id: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
                            name: 'Organization 1',
                            country: 'FRA',
                            location: 'location 1',
                            type: 'B2B',
                            cellId: 'test2',
                            status: 'RGS',
                            createdAt: '2023-07-25T13:39:52Z',
                            createdBy: 'test@intel.com',
                            modifiedAt: null,
                            modifiedBy: '',
                        },
                    ],
                    totalCount: 1,
                    nextPage: {
                        skip: 0,
                        limit: 0,
                    },
                })
            );
        }
        case '/profile': {
            return res(
                ctx.status(200),
                ctx.json({
                    organizations: [
                        {
                            organizationName: 'Organization 1',
                            userStatus: 'ACT',
                            organizationStatus: 'ACT',
                            organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
                            organizationCreatedAt: '2024-10-04T10:04:24Z',
                        },
                    ],
                    telemetryConsent: 'y',
                    telemetryConsentAt: '2023-11-02T10:03:47.428474Z',
                    userConsent: 'y',
                    userConsentAt: '2023-11-02T10:03:47.428474Z',
                })
            );
        }
        case '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633': {
            return res(
                ctx.status(200),
                ctx.json({
                    id: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
                    name: 'Organization 1',
                    country: 'FRA',
                    location: 'location 1',
                    type: 'B2B',
                    cellId: 'test2',
                    status: 'RGS',
                    createdAt: '2023-07-25T13:39:52Z',
                    createdBy: 'test@intel.com',
                    modifiedAt: null,
                    modifiedBy: '',
                })
            );
        }
        case '/set_cookie': {
            return res(ctx.status(200));
        }
        case '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/subscriptions/active/quotas': {
            return res(
                ctx.json({
                    next_page: null,
                    quotas: [],
                    total_matched: 0,
                })
            );
        }
        default: {
            if (/pipelines\/.*\/status/.test(c.request.path)) {
                return res(ctx.status(200), ctx.json({ pipeline_ready: true }));
            }

            console.warn(
                `
                    Handler for path "${c.request.path}" not found.
                    What you can do:
                    * Add the definition to the respective api spec
                    or
                    * Add a specific handler on 'setup-open-api-handlers.ts'`
            );

            return res(ctx.status(404));
        }
    }
};

const registerDefaultHandlers = (api: OpenAPIBackend) => {
    api.register('notFound', notFoundHandler);

    const returnImage: OperationHandler = async (_: Context<Document>, res, ctx) => {
        const imageBuffer = fs.readFileSync(path.resolve(__dirname, '../../../src/assets/tests-assets/antelope.webp'));

        return res(
            ctx.set('Content-Length', imageBuffer.byteLength.toString()),
            ctx.set('Content-Type', 'image/jpeg'),
            ctx.body(imageBuffer)
        );
    };

    // Overwriting these settings makes sure that we don't show the first user
    // experience dialogs when testing the application.
    // For tests where we do want to test the first user experience we should
    // overwrite this operation
    const getSettings: OperationHandler = async (_: Context<Document>, res, ctx) => {
        return res(ctx.json({ settings }));
    };

    const FilterMedia: OperationHandler = (_, res, ctx) => {
        const { mock, status } = api.mockResponseForOperation('FilterMedia');

        // By default, the FilterMedia operation's example returns a next page,
        // we don't want this as we always return the same response, which would
        // lead to an infinite loop whenever the media page is loaded
        delete mock.next_page;

        return res(ctx.status(status), ctx.json(mock));
    };

    const GetSupportedAlgorithms: OperationHandler = async (_: Context<Document>, res, ctx) => {
        return res(ctx.json(supportedAlgorithms));
    };

    api.register({
        GetSettings: getSettings,
        DownloadProjectThumbnail: returnImage,
        DownloadVideoFrameFull: returnImage,
        DownloadVideoFrameThumbnail: returnImage,
        DownloadVideoThumbnail: returnImage,
        DownloadFullImage: returnImage,
        DownloadImageThumbnail: returnImage,
        DownloadVideoStream: async (_, res, ctx) => {
            return res(ctx.status(404));
        },
        FilterMedia,
        GetSupportedAlgorithms,
        GetOrganizationStatus: async (_, res, ctx) => {
            return res(
                ctx.json({ storage: { free_space: 2000000000000, total_space: 2000000000000 }, n_running_jobs: 0 })
            );
        },
        GetServerStatus: async (_, res, ctx) => {
            return res(
                ctx.json({ storage: { free_space: 2000000000000, total_space: 2000000000000 }, n_running_jobs: 0 })
            );
        },
        User_get_user_profile: async (_, res, ctx) => {
            return res(
                ctx.json({
                    organizations: [
                        {
                            organizationName: 'Organization 1',
                            userStatus: 'ACT',
                            organizationStatus: 'ACT',
                            organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
                            organizationCreatedAt: '2024-10-04T10:04:24Z',
                        },
                    ],
                    telemetryConsent: 'y',
                    telemetryConsentAt: '2023-11-02T10:03:47.428474Z',
                    userConsent: 'y',
                    userConsentAt: '2023-11-02T10:03:47.428474Z',
                })
            );
        },
        User_get_active_user: async (_, res, ctx) => {
            // These roles are picked so that the default user in our tests has
            // as many permissions as possible, in particular we give the user
            // an admin role to all resources used in our tests
            const roles = [
                { role: 'admin', resourceType: 'user_directory', resourceId: 'global' },
                {
                    role: 'organization_admin',
                    resourceType: 'organization',
                    resourceId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
                },
                { role: 'workspace_admin', resourceType: 'workspace', resourceId: '61012cdb1d38a5e71ef3baf9' },
                { role: 'workspace_admin', resourceType: 'workspace', resourceId: '61011e42d891c82e13ec92da' },
                { role: 'workspace_admin', resourceType: 'workspace', resourceId: '61011e43d891c82e13ec952e' },
            ];

            return res(
                ctx.json({
                    id: '77b5fa42-599e-4899-a4c0-daae13487289',
                    firstName: 'admin',
                    secondName: 'admin',
                    email: 'admin@intel.com',
                    externalId: '<redacted>',
                    country: 'POL',
                    status: 'ACT',
                    organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
                    organizationStatus: '',
                    roles,
                    lastSuccessfulLogin: null,
                    currentSuccessfulLogin: null,
                    createdAt: '2024-02-20T11:42:28Z',
                    createdBy: '',
                    modifiedAt: '2024-02-20T11:42:29Z',
                    modifiedBy: '',
                    telemetryConsent: '',
                    telemetryConsentAt: null,
                    userConsent: '',
                    userConsentAt: null,
                    presignedUrl: '',
                })
            );
        },
        Workspace_find: async (_, res, ctx) => {
            return res(
                ctx.json({
                    workspaces: [
                        {
                            creation_date: '2021-07-28T09:07:13.999000+00:00',
                            creator_name: 'dummy',
                            description: 'This is the first workspace.',
                            id: '61011e42d891c82e13ec92da',
                            name: 'Workspace 1',
                        },
                        {
                            creation_date: '2021-07-28T09:07:15.985000+00:00',
                            creator_name: 'dummy',
                            description: 'This is another workspace.',
                            id: '61011e43d891c82e13ec952e',
                            name: 'Workspace 2',
                        },
                    ],
                })
            );
        },
        get_balance_api_v1_organizations__org_id__balance_get: async (_, res, ctx) => {
            return res(ctx.json({ incoming: 3000, available: 3000 }));
        },
    });
};

export const setupOpenApiHandler = async (): Promise<OpenAPIBackend<Document>> => {
    const options: Options = { definition } as unknown as Options;

    if (isString(options.definition) || options.definition.servers === undefined) {
        throw new Error('Invalid openapi server definitions');
    }

    options.definition.servers.forEach((server) => {
        server.url = 'http://localhost:3000/api/v1';
    });

    // Skip precompiling Ajv validators, this saves about 3~5 seconds
    // of init time
    options.quick = true;
    options.validate = false;
    options.strict = false;

    const api = new OpenAPIBackend(options);

    registerDefaultHandlers(api);

    // Keep track of operations that we did not register and use the schema's
    // example response as a mock
    const operations = new Set<string>();
    const notImplementedHandler: OperationHandler = (c, res, ctx) => {
        const operationId = c.operation.operationId;

        if (!operationId) {
            return;
        }

        // Log all operations that were not implemented for the current test
        if (!operations.has(operationId)) {
            if (SHOW_UNIMPLEMENTED_OPERATIONS) {
                // eslint-disable-next-line no-console
                console.log(`[${operationId}]`);
            }

            operations.add(operationId);
        }

        const { status, mock } = c.api.mockResponseForOperation(operationId);

        return res(ctx.status(status), ctx.json(mock));
    };

    api.register('notImplemented', notImplementedHandler);

    api.definition = options.definition;

    await api.init();

    return api;
};
