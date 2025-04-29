// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { OrganizationIdentifier } from '../../organizations/organizations.interface';

export interface WorkspaceIdentifier extends OrganizationIdentifier {
    workspaceId: string;
}

export interface Workspace {
    id: string;
    name: string;
}

export interface WorkspaceEntity extends Workspace {
    organizationId: string;
    createdAt: string;
    createdBy: string;
    modifiedAt: string;
    modifiedBy: string;
}
