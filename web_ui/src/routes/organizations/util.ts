// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { AccountStatus } from '../../core/organizations/organizations.interface';
import { OrganizationMetadata } from '../../core/users/services/onboarding-service.interface';

export const isOrganizationVisible = (organization: OrganizationMetadata) =>
    organization.status === AccountStatus.ACTIVATED || isInvitedOrganization(organization);

export const isInvitedOrganization = ({ status }: OrganizationMetadata) => status === AccountStatus.INVITED;

export const isUserInvitedInOrg = ({ userStatus }: OrganizationMetadata) => userStatus === AccountStatus.INVITED;

export const isUserActivatedInOrg = ({ userStatus }: OrganizationMetadata) => userStatus === AccountStatus.ACTIVATED;

export const isOrgVisibleAndUserActivatedInOrg = (organization: OrganizationMetadata) =>
    isOrganizationVisible(organization) && isUserActivatedInOrg(organization);

export const isOrgVisibleAndUserInvitedInOrg = (organization: OrganizationMetadata) =>
    isOrganizationVisible(organization) && isUserInvitedInOrg(organization);
