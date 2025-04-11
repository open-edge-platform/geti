// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useState } from 'react';

import { DialogContainer } from '@adobe/react-spectrum';

import { ProjectIdentifier } from '../../../../core/projects/core.interface';
import { useProjectActions } from '../../../../core/projects/hooks/use-project-actions.hook';
import { RESOURCE_TYPE } from '../../../../core/users/users.interface';
import { useFirstWorkspaceIdentifier } from '../../../../providers/workspaces-provider/use-first-workspace-identifier.hook';
import { ActionMenu } from '../../../../shared/components/action-menu/action-menu.component';
import { useCheckPermission } from '../../../../shared/components/has-permission/has-permission.component';
import { OPERATION } from '../../../../shared/components/has-permission/has-permission.interface';
import { DeleteProjectDialog } from '../../../landing-page/landing-page-workspace/components/projects-list/components/project/components/project-action-menu/delete-project-dialog.component';

export const ProjectActionCell = ({ name, id }: { name: string; id: string }): JSX.Element => {
    const workspaceIdentifier = useFirstWorkspaceIdentifier();
    const [isDeleteAlertVisible, setIsDeleteAlertVisible] = useState<boolean>(false);
    const canDeleteProject = useCheckPermission([OPERATION.PROJECT_DELETION], [{ type: RESOURCE_TYPE.PROJECT, id }]);
    const { deleteProjectMutation } = useProjectActions();

    if (!canDeleteProject) {
        return <></>;
    }

    const handleAction = () => {
        setIsDeleteAlertVisible(true);
    };

    const handleDeleteProject = (projectIdentifier: ProjectIdentifier, onSuccess: () => void) => {
        deleteProjectMutation.mutate(projectIdentifier, { onSuccess });
    };

    return (
        <>
            <ActionMenu
                id={`project-storage-action-${id}`}
                items={[{ name: 'Delete', id: `delete-${id}` }]}
                onAction={handleAction}
            />
            <DialogContainer onDismiss={() => setIsDeleteAlertVisible(false)}>
                {isDeleteAlertVisible && (
                    <DeleteProjectDialog
                        projectIdentifier={{ ...workspaceIdentifier, projectId: id }}
                        onDeleteProject={handleDeleteProject}
                        projectName={name}
                    />
                )}
            </DialogContainer>
        </>
    );
};
