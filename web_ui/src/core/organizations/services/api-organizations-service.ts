// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { instance as defaultAxiosInstance } from '../../services/axios-instance';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { OrganizationDTO, OrganizationsResponseDTO } from '../dtos/organizations.interface';
import { Organization } from '../organizations.interface';
import { OrganizationsService } from './organizations-service.interface';
import {
    getOrganizationEntity,
    getOrganizationInvitationPayload,
    getOrganizationsEntity,
    getOrganizationsEntityDTO,
} from './utils';

export const createApiOrganizationsService: CreateApiService<OrganizationsService> = (
    { instance: platformInstance, router } = { instance: defaultAxiosInstance, router: API_URLS }
) => {
    const getOrganizations: OrganizationsService['getOrganizations'] = async (queryOptions) => {
        const { data } = await platformInstance.get<OrganizationsResponseDTO>(`${router.ORGANIZATIONS}`, {
            params: queryOptions,
        });

        return getOrganizationsEntity(data);
    };

    const getOrganization: OrganizationsService['getOrganization'] = async (organizationId: string) => {
        const { data } = await platformInstance.get<OrganizationDTO>(router.ORGANIZATION(organizationId));

        return getOrganizationEntity(data);
    };

    const deleteOrganization: OrganizationsService['deleteOrganization'] = async (organizationId: string) => {
        await platformInstance.delete<string>(router.ORGANIZATION(organizationId));
    };

    const updateOrganization: OrganizationsService['updateOrganization'] = async (organization: Organization) => {
        const { data } = await platformInstance.put<OrganizationDTO>(
            router.ORGANIZATION(organization.id),
            getOrganizationsEntityDTO(organization)
        );

        return getOrganizationEntity(data);
    };

    const inviteOrganization: OrganizationsService['inviteOrganization'] = async (
        organizationName: string,
        adminEmail: string
    ) => {
        const payload = getOrganizationInvitationPayload(organizationName, adminEmail);

        await platformInstance.post<void>(router.INVITE_ORGANIZATION, payload);
    };

    return {
        getOrganizations,
        getOrganization,
        updateOrganization,
        deleteOrganization,
        inviteOrganization,
    };
};
