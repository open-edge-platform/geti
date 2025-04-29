// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Resource, RESOURCE_TYPE, Role } from '../../../core/users/users.interface';

export interface HasPermissionProps {
    children: ReactNode;
    operations: OPERATION[];
    Fallback?: ReactNode;
    resources?: Resource[];
    specialCondition?: boolean;
}

export enum OPERATION {
    INVITE_USER,
    MANAGE_USER,
    WORKSPACE_MANAGEMENT,
    IMPORT_PROJECT,
    ADD_USER_TO_PROJECT,
    PROJECT_CREATION,
    PROJECT_DELETION,
    CAN_VIEW_CREDITS_USAGE,
    PROJECT_NAME_EDITION,
    USAGE_TAB,
    ANALYTICS_TAB,
}

type PermissionEntity = Omit<Role, 'resourceId'>;

export type OperationPermission = Record<OPERATION, PermissionEntity[]>;

export type UsePermissionType = {
    verifyPermission: (operation: OPERATION, resources: Record<RESOURCE_TYPE, string | undefined>) => boolean;
};
