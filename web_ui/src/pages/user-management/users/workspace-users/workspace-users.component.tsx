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

import { RESOURCE_TYPE, User } from '../../../../core/users/users.interface';
import { useIsSaasEnv } from '../../../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { USERS_TABLE_COLUMNS } from '../users-table/users-table.component';
import { Users } from '../users.component';
import { WorkspaceUserActions } from './actions/workspace-user-actions.component';

interface WorkspaceUsersProps {
    activeUser: User;
    workspaceId: string | undefined;
}

export const WorkspaceUsers = ({ activeUser, workspaceId }: WorkspaceUsersProps): JSX.Element => {
    const isSaasEnv = useIsSaasEnv();

    return (
        <Users
            activeUser={activeUser}
            resourceType={RESOURCE_TYPE.WORKSPACE}
            resourceId={workspaceId}
            UserActions={WorkspaceUserActions}
            ignoredColumns={isSaasEnv ? undefined : [USERS_TABLE_COLUMNS.LAST_LOGIN]}
        />
    );
};
