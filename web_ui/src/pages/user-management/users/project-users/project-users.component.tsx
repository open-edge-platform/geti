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

import { useUsers } from '../../../../core/users/hook/use-users.hook';
import { RESOURCE_TYPE, User } from '../../../../core/users/users.interface';
import { useIsSaasEnv } from '../../../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { HasPermission } from '../../../../shared/components/has-permission/has-permission.component';
import { OPERATION } from '../../../../shared/components/has-permission/has-permission.interface';
import { PageLayout } from '../../../../shared/components/page-layout/page-layout.component';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { USERS_TABLE_COLUMNS } from '../users-table/users-table.component';
import { Users } from '../users.component';
import { Header } from './header.component';
import { ProjectUserActions } from './project-user-actions.component';

export const ProjectUsers = (): JSX.Element => {
    const {
        projectIdentifier: { organizationId, projectId },
    } = useProject();
    const { useActiveUser } = useUsers();
    const { data: activeUser } = useActiveUser(organizationId);
    const isSaasEnv = useIsSaasEnv();

    const ignoredColumns = isSaasEnv
        ? [USERS_TABLE_COLUMNS.REGISTRATION_STATUS]
        : [USERS_TABLE_COLUMNS.REGISTRATION_STATUS, USERS_TABLE_COLUMNS.LAST_LOGIN];

    if (activeUser === undefined) {
        return <></>;
    }

    return (
        <PageLayout
            breadcrumbs={[{ id: 'users-id', breadcrumb: 'Users' }]}
            header={
                <HasPermission
                    operations={[OPERATION.ADD_USER_TO_PROJECT]}
                    resources={[{ type: RESOURCE_TYPE.PROJECT, id: projectId }]}
                >
                    <Header />
                </HasPermission>
            }
        >
            <Users
                activeUser={activeUser as User}
                resourceType={RESOURCE_TYPE.PROJECT}
                resourceId={projectId}
                ignoredColumns={ignoredColumns}
                isProjectUsersTable
                UserActions={ProjectUserActions}
            />
        </PageLayout>
    );
};
