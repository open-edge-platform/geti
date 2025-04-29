// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AccountStatus } from '../../core/organizations/organizations.interface';
import { OrganizationMetadata } from '../../core/users/services/onboarding-service.interface';

export const isActiveOrganization = (organization: OrganizationMetadata) =>
    organization.status === AccountStatus.ACTIVATED;

export const isOrganizationVisible = (organization: OrganizationMetadata) =>
    isActiveOrganization(organization) || isInvitedOrganization(organization);

export const isInvitedOrganization = ({ status }: OrganizationMetadata) => status === AccountStatus.INVITED;

export const isUserInvitedInOrg = ({ userStatus }: OrganizationMetadata) => userStatus === AccountStatus.INVITED;

export const isUserActivatedInOrg = ({ userStatus }: OrganizationMetadata) => userStatus === AccountStatus.ACTIVATED;

export const isOrgVisibleAndUserActivatedInOrg = (organization: OrganizationMetadata) =>
    isOrganizationVisible(organization) && isUserActivatedInOrg(organization);

export const isOrgVisibleAndUserInvitedInOrg = (organization: OrganizationMetadata) =>
    isOrganizationVisible(organization) && isUserInvitedInOrg(organization);
