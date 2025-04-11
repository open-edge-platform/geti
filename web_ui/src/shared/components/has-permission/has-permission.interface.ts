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
