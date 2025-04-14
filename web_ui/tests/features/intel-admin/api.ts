// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    AccountStatusDTO,
    OrganizationDTO,
    OrganizationsResponseDTO,
} from '../../../src/core/organizations/dtos/organizations.interface';
import { OpenApiRequest } from '../../../src/core/server/types';
import { getMockedOrganizationDTO } from '../../../src/test-utils/mocked-items-factory/mocked-organization';
import { getMockedAdminUser } from '../../../src/test-utils/mocked-items-factory/mocked-users';
import { OpenApiFixtures } from '../../fixtures/open-api';
import { mockedOrganizationsResponse } from './mocks';

const filterOrganizationsResponse = (req: OpenApiRequest<'Organization_find'>, organizations: OrganizationDTO[]) => {
    let filteredOrganizations: OrganizationDTO[] = [...organizations];

    if (req.query.name) {
        filteredOrganizations = organizations.filter(
            (organization) => organization.name === req.query.name || organization.admins[0].email === req.query.name
        );
    }

    if (req.query.status) {
        filteredOrganizations = organizations.filter((organization) => organization.status === req.query.status);
    }

    return {
        ...mockedOrganizationsResponse,
        totalMatchedCount: filteredOrganizations.length,
        organizations: filteredOrganizations,
    };
};

export const registerApiOrganizations = ({
    registerApiResponse,
    inputOrganizations = mockedOrganizationsResponse,
}: {
    registerApiResponse: OpenApiFixtures['registerApiResponse'];
    inputOrganizations?: OrganizationsResponseDTO;
}) => {
    const initialOrganizationResponse = structuredClone(inputOrganizations);
    let organizations = initialOrganizationResponse.organizations;

    registerApiResponse('Organization_find', (req, res, ctx) => {
        const newOrganizationsPayload = filterOrganizationsResponse(req, organizations);
        organizations = newOrganizationsPayload.organizations;

        return res(ctx.json(newOrganizationsPayload));
    });

    registerApiResponse('Organization_modify', (req, res, ctx) => {
        const updatedOrganization = getMockedOrganizationDTO(req.body as OrganizationDTO);
        organizations = organizations.map((organization) => {
            if (organization.id === req.params.id) {
                return updatedOrganization;
            }

            return organization;
        });

        // @ts-expect-error Issue in OpenApi types
        return res(ctx.json(updatedOrganization));
    });

    registerApiResponse('Organization_send_invitation', (req, res, ctx) => {
        const newOrganization = getMockedOrganizationDTO({
            name: req?.body?.organizationData?.name,
            admins: [
                getMockedAdminUser({
                    firstName: 'Chris',
                    lastName: 'Sawyer',
                    email: req.body.adminData?.email,
                }),
            ],
            status: AccountStatusDTO.REGISTERED,
        });

        organizations.push(newOrganization);

        return res(ctx.status(200));
    });

    return {
        get() {
            return organizations;
        },
        reset() {
            organizations = initialOrganizationResponse.organizations;
        },
    };
};
