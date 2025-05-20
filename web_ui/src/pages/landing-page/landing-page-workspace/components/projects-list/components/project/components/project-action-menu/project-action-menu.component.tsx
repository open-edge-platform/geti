// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useMemo, useState } from 'react';

import { DialogContainer } from '@geti/ui';
import { isEmpty } from 'lodash-es';
import { useOverlayTriggerState } from 'react-stately';

import { ProjectIdentifier } from '../../../../../../../../../core/projects/core.interface';
import { ProjectProps } from '../../../../../../../../../core/projects/project.interface';
import { RESOURCE_TYPE } from '../../../../../../../../../core/users/users.interface';
import { useWorkspaceIdentifier } from '../../../../../../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { ActionMenu } from '../../../../../../../../../shared/components/action-menu/action-menu.component';
import { MenuAction } from '../../../../../../../../../shared/components/action-menu/menu-action.interface';
import { useCheckPermission } from '../../../../../../../../../shared/components/has-permission/has-permission.component';
import { OPERATION } from '../../../../../../../../../shared/components/has-permission/has-permission.interface';
import { DeleteProjectDialog } from './delete-project-dialog.component';
import { EditProjectNameDialog } from './edit-project-name-dialog.component';

interface ActionMenuProps {
    project: ProjectProps;
    isExporting: boolean;
    onExportProject: (projectIdentifier: ProjectIdentifier) => void;
    onDeleteProject: (projectIdentifier: ProjectIdentifier, onSuccess: () => void) => void;
}

enum ProjectActions {
    Delete = 'Delete',
    Export = 'Export',
    Rename = 'Rename',
}

const ITEMS = [
    { name: ProjectActions.Export, id: ProjectActions.Export },
    { name: ProjectActions.Delete, id: ProjectActions.Delete },
    { name: ProjectActions.Rename, id: ProjectActions.Rename },
];

export const ProjectActionMenu = ({
    project,
    onExportProject,
    onDeleteProject,
    isExporting,
}: ActionMenuProps): JSX.Element => {
    const { workspaceId, organizationId } = useWorkspaceIdentifier();
    const canEditProject = useCheckPermission(
        [OPERATION.PROJECT_NAME_EDITION],
        [{ type: RESOURCE_TYPE.PROJECT, id: project.id }]
    );
    const canDeleteProject = useCheckPermission(
        [OPERATION.PROJECT_DELETION],
        [{ type: RESOURCE_TYPE.PROJECT, id: project.id }]
    );

    const [isAlertOpen, setIsAlertOpen] = useState(false);
    const editProjectNameDialogState = useOverlayTriggerState({});
    const disabledKeys = isExporting ? [ProjectActions.Export] : [];

    const items: MenuAction<ProjectActions>[] = useMemo<MenuAction<ProjectActions>[]>(
        (): MenuAction<ProjectActions>[] =>
            ITEMS.filter((item: Record<string, string>): boolean => {
                if (item.id === ProjectActions.Delete) {
                    return canDeleteProject;
                }

                if (item.id === ProjectActions.Rename) {
                    return canEditProject;
                }

                return true;
            }),
        [canDeleteProject, canEditProject]
    );

    const onOpenDialog = (tap: Key) => {
        switch (tap) {
            case ProjectActions.Delete:
                setIsAlertOpen(true);
                break;
            case ProjectActions.Export:
                onExportProject({ organizationId, workspaceId, projectId: project.id });
                break;
            case ProjectActions.Rename:
                editProjectNameDialogState.open();
                break;
        }
    };

    return !isEmpty(items) ? (
        <>
            <ActionMenu<ProjectActions>
                items={items}
                id={`project-action-menu-${project.id}`}
                disabledKeys={disabledKeys}
                onAction={onOpenDialog}
                tooltipMessage='Project menu'
            />
            <DialogContainer onDismiss={() => setIsAlertOpen(false)}>
                {isAlertOpen && (
                    <DeleteProjectDialog
                        projectIdentifier={{ organizationId, projectId: project.id, workspaceId }}
                        onDeleteProject={onDeleteProject}
                        projectName={project.name}
                    />
                )}
            </DialogContainer>

            {canEditProject && (
                <EditProjectNameDialog
                    project={project}
                    onClose={editProjectNameDialogState.close}
                    isOpen={editProjectNameDialogState.isOpen}
                />
            )}
        </>
    ) : (
        <></>
    );
};
