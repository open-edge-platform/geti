// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Resource, RESOURCE_TYPE, Role } from '@geti/core/src/users/users.interface';

export interface HasPermissionProps {
    children: ReactNode;
    operations: (OPERATION_NEW | OPERATION_OLD)[];
    Fallback?: ReactNode;
    resources?: Resource[];
    specialCondition?: boolean;
}

export enum OPERATION_NEW {
    ADD_USER_TO_WORKSPACE,
    ADD_USER_TO_PROJECT,
    ANALYTICS_TAB,
    CAN_SEE_PROJECT,
    CAN_SEE_WORKSPACE,
    CAN_VIEW_CREDITS_USAGE,
    INVITE_USER,
    IMPORT_PROJECT,
    MANAGE_USER,
    PROJECT_CREATION,
    PROJECT_DELETION,
    PROJECT_NAME_EDITION,
    USAGE_TAB,
    WORKSPACE_MANAGEMENT,
    WORKSPACE_CREATION,
}

export enum OPERATION_OLD {
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

export type OperationPermissionOld = Record<OPERATION_OLD, PermissionEntity[]>;
export type OperationPermissionNew = Record<OPERATION_NEW, PermissionEntity[]>;

export type UsePermissionType = {
    verifyPermission: (
        operation: OPERATION_NEW | OPERATION_OLD,
        resources: Record<RESOURCE_TYPE, string | undefined>
    ) => boolean;
};
