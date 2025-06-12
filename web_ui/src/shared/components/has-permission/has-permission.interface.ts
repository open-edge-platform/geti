// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Resource, RESOURCE_TYPE, Role } from '@geti/core/src/users/users.interface';

export interface HasPermissionProps {
    children: ReactNode;
    operations: OPERATION[];
    Fallback?: ReactNode;
    resources?: Resource[];
    specialCondition?: boolean;
}

export enum OPERATION {
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

type PermissionEntity = Omit<Role, 'resourceId'>;

export type OperationPermission = Record<OPERATION, PermissionEntity[]>;
export type OperationPermissionOld = Record<
    Exclude<
        OPERATION,
        | OPERATION.ADD_USER_TO_WORKSPACE
        | OPERATION.CAN_SEE_PROJECT
        | OPERATION.CAN_SEE_WORKSPACE
        | OPERATION.WORKSPACE_CREATION
    >,
    PermissionEntity[]
>;

export type UsePermissionType = {
    verifyPermission: (operation: OPERATION, resources: Record<RESOURCE_TYPE, string | undefined>) => boolean;
};
