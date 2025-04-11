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

import { RESOURCE_TYPE, USER_ROLE } from '../../../core/users/users.interface';
import { OPERATION, OperationPermission } from './has-permission.interface';

export const ORGANIZATION_ADMIN_PERMISSION = {
    role: USER_ROLE.ORGANIZATION_ADMIN,
    resourceType: RESOURCE_TYPE.ORGANIZATION,
};

export const WORKSPACE_ADMIN_PERMISSION = {
    role: USER_ROLE.WORKSPACE_ADMIN,
    resourceType: RESOURCE_TYPE.WORKSPACE,
};

export const WORKSPACE_CONTRIBUTOR_PERMISSION = {
    role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
    resourceType: RESOURCE_TYPE.WORKSPACE,
};

export const PROJECT_MANAGER_PERMISSION = {
    role: USER_ROLE.PROJECT_MANAGER,
    resourceType: RESOURCE_TYPE.PROJECT,
};

const canManageProject = [ORGANIZATION_ADMIN_PERMISSION, WORKSPACE_ADMIN_PERMISSION, PROJECT_MANAGER_PERMISSION];
const canCreateProject = [WORKSPACE_ADMIN_PERMISSION, WORKSPACE_CONTRIBUTOR_PERMISSION];

export const OPERATION_PERMISSION: OperationPermission = {
    [OPERATION.INVITE_USER]: [ORGANIZATION_ADMIN_PERMISSION],
    [OPERATION.MANAGE_USER]: [ORGANIZATION_ADMIN_PERMISSION],
    [OPERATION.WORKSPACE_MANAGEMENT]: [WORKSPACE_ADMIN_PERMISSION],
    [OPERATION.IMPORT_PROJECT]: [WORKSPACE_ADMIN_PERMISSION],
    [OPERATION.ADD_USER_TO_PROJECT]: canManageProject,
    [OPERATION.PROJECT_CREATION]: canCreateProject,
    [OPERATION.PROJECT_DELETION]: canManageProject,
    [OPERATION.CAN_VIEW_CREDITS_USAGE]: [ORGANIZATION_ADMIN_PERMISSION, WORKSPACE_ADMIN_PERMISSION],
    [OPERATION.PROJECT_NAME_EDITION]: [WORKSPACE_ADMIN_PERMISSION, PROJECT_MANAGER_PERMISSION],
    [OPERATION.USAGE_TAB]: [ORGANIZATION_ADMIN_PERMISSION, WORKSPACE_ADMIN_PERMISSION],
    [OPERATION.ANALYTICS_TAB]: [ORGANIZATION_ADMIN_PERMISSION, WORKSPACE_ADMIN_PERMISSION],
};
