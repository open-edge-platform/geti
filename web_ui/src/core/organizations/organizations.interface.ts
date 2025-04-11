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

// NOTE: This interface are mostly the same as DTO interfaces, but I wanted to create a new "application layer",
// so we don't need to rely on backend DTOs, and we can structure it how we want.

import { InfiniteQuery } from '../shared/infinite-query.interface';
import { OrganizationAdmin } from './dtos/organizations.interface';

export enum AccountStatus {
    INVITED = 'Invited',
    ACTIVATED = 'Activated',
    SUSPENDED = 'Suspended',
    DELETED = 'Deleted',
    REQUESTED_ACCESS = 'Requested access',
}

export enum OrganizationType {
    BUSINESS_TO_BUSINESS = 'Business to Business',
    BUSINESS_TO_CLIENT = 'Business to Client',
}

export interface Organization {
    id: string;
    name: string;
    country: string;
    admins: OrganizationAdmin[];
    location: string;
    type: OrganizationType;
    cellId: string;
    status: AccountStatus;
    createdAt: string;
    createdBy: string;
    modifiedAt: string;
    modifiedBy: string;
    requestAccessReason: string;
}

export interface OrganizationsResponse extends InfiniteQuery {
    organizations: Organization[];
    totalMatchedCount: number;
}

export interface OrganizationIdentifier {
    organizationId: string;
}

export interface OrganizationInvitationPayload {
    organizationData: {
        name: string;
    };
    adminData: {
        email: string;
    };
}
