// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { OpenApiFixtures } from '../../fixtures/open-api';
import { project } from '../../mocks/segmentation/mocks';

const ORGANIZATION_ID = '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633';
const WORKSPACE_ID = '61011e42d891c82e13ec92da';
const PROJECT_ID = project.id;
export { project };

const commonUserProperties = {
    externalId: '',
    country: '',
    status: 'ACT',
    organizationId: '14b951d9-8a7e-4fe8-870f-99c4abf0626e',
    organizationStatus: 'ACT',
    lastSuccessfulLogin: null,
    currentSuccessfulLogin: null,
    createdAt: null,
    createdBy: '',
    modifiedAt: null,
    modifiedBy: '',
    telemetryConsent: '',
    telemetryConsentAt: null,
    userConsent: '',
    userConsentAt: null,
    presignedUrl: '',
};

const getUsers = () => [
    {
        id: '43fc5d9c-4db1-48e8-bebb-d625f6a5dadc',
        firstName: 'admin',
        secondName: 'admin',
        email: 'admin@intel.com',
        ...commonUserProperties,
        roles: [
            { role: 'organization_admin', resourceType: 'organization', resourceId: ORGANIZATION_ID },
            { role: 'workspace_admin', resourceType: 'workspace', resourceId: WORKSPACE_ID },
            { role: 'project_admin', resourceType: 'project', resourceId: PROJECT_ID },
        ],
    },
    {
        id: '1c50b7d6-3e8e-40c8-966d-38d68c68df58',
        firstName: 'Test',
        secondName: 'User',
        email: 'test@intel.com',
        ...commonUserProperties,
        roles: [
            { role: 'organization_contributor', resourceType: 'organization', resourceId: ORGANIZATION_ID },
            { role: 'workspace_contributor', resourceType: 'workspace', resourceId: WORKSPACE_ID },
        ],
    },
    {
        id: 'a3ce97da-a6ea-43be-aba1-5e5c660ad6c1',
        firstName: 'Test',
        secondName: 'User 2',
        email: 'test2@intel.com',
        ...commonUserProperties,
        roles: [
            { role: 'organization_contributor', resourceType: 'organization', resourceId: ORGANIZATION_ID },
            { role: 'workspace_contributor', resourceType: 'workspace', resourceId: WORKSPACE_ID },
            { role: 'project_contributor', resourceType: 'project', resourceId: PROJECT_ID },
        ],
    },
];

export const registerUserApis = (
    registerApiResponse: OpenApiFixtures['registerApiResponse'],
    activeUserUid: string
) => {
    const users = getUsers();

    registerApiResponse('User_find', (req, res, ctx) => {
        const resourceUsers = users
            .map((user) => {
                const roles = user.roles.filter(({ resourceType }) => resourceType === req.query.resourceType);
                return { ...user, roles };
            })
            .filter(({ roles }) => roles.length > 0)
            .filter((user) => {
                if (req.query.name) {
                    return user.email.includes(req.query.name);
                }
                return true;
            });

        return res(
            ctx.json({
                users: resourceUsers,
                totalCount: resourceUsers.length,
                totalMatchedCount: resourceUsers.length,
                nextPage: {
                    skip: 20,
                    limit: 0,
                },
            })
        );
    });

    registerApiResponse('User_get_active_user', (_, res, ctx) => {
        const activeUser = users.find(({ email }) => email === activeUserUid);

        if (activeUser === undefined) {
            return res(ctx.status(404));
        }

        return res(ctx.json(activeUser));
    });

    registerApiResponse('User_set_roles', (req, res, ctx) => {
        const user = users.find(({ id }) => id === req.params.userId);

        if (user === undefined) {
            return res(ctx.status(404));
        }

        const requestRoles = req.body.roles ?? [];

        const newRoles = requestRoles.filter((role) => {
            return (
                (role.operation === 'TOUCH' || role.operation === 'CREATE') &&
                user.roles.some(
                    (userRole) =>
                        !(
                            userRole.resourceId === role.role?.resourceId &&
                            userRole.resourceType === role.role?.resourceType
                        )
                )
            );
        });
        const existingRoles = requestRoles.filter((role) => {
            return user.roles.some(
                (userRole) =>
                    userRole.resourceId === role.role?.resourceId && userRole.resourceType === role.role?.resourceType
            );
        });

        user.roles = user.roles.filter((userRole) => {
            const overWritten = existingRoles.find(
                (role) =>
                    userRole.resourceId === role.role?.resourceId && userRole.resourceType === role.role?.resourceType
            );

            return !(overWritten && overWritten.operation === 'DELETE');
        });

        newRoles.forEach(({ role }) => {
            // @ts-expect-error role is always defined
            user.roles.push(role);
        });

        return res(ctx.status(200), ctx.json({}));
    });
};
