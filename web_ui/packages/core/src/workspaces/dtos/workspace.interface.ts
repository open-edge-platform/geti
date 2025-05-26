// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { InfiniteQueryDTO } from '../../../../../src/core/shared/dto/infinite-query.interface';

export interface WorkspaceDTO {
    id: string;
    name: string;
    organizationId: string;
    createdAt: string;
    createdBy: string;
    modifiedAt: string;
    modifiedBy: string;
}

export interface WorkspacesResponseDTO extends InfiniteQueryDTO {
    workspaces: WorkspaceDTO[];
}
