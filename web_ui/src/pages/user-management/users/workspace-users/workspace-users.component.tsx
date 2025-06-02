// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RESOURCE_TYPE, User } from '@geti/core/src/users/users.interface';

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
